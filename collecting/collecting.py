#!/usr/bin/env python

import scraperwiki
import requests
import json
import os
import dateutil.parser
import re

# Get a token.  Make sure not to save any tokens here.
api_token = ''
if 'GITHUB_TOKEN' in os.environ:
  api_token = os.environ['GITHUB_TOKEN']

# List of users/orgs that we want to track
accounts = ['minnpost', 'nytimes', 'propublica', 'datadesk', 'texastribune', 'newsapps', 'nprapps', 'wnyc', 'washingtonpost', 'guardian', 'openNews', 'documentcloud', 'ajam', 'sourcefabric', 'quartz', 'censusreporter', 'ireapps', 'datawrapper', 'TheAssociatedPress', 'ZeitOnline', 'overview', 'huffpostdata', 'poderopedia', 'LearningLab', 'glasseyemedia', 'stateimpact', 'freedomofpress', 'NUKnightLab', 'superdesk', 'nacion', 'cirlabs', 'BBC-News', 'SCPR', 'PRX', 'vprnet', 'buzzfeednews', 'mcclatchy', 'registerguard', 'dallasmorningnews', 'voxmedia', 'fivethirtyeight', 'theupshot', 'thunderdome-data', 'sunlightlabs', 'inn', 'stlpublicradio']
old_accounts = ['guardianinteractive']

# Print json nicely
def print_json(parsed):
  print json.dumps(parsed, indent = 4, sort_keys = True)


# Parse link headers, as they are weird
def parse_link_header(header = None):
  if header is None or header == '':
    return None

  parsed = {}
  found = re.findall('(<(.*?)>; rel="(\w+)")+', header)
  if found is not None:
    for f in found:
      parsed[f[2]] = f[1]

  return parsed


# Make a request
def make_request(method, params = {}, collected = []):
  # Allow for simple method call, or for a whole http request
  call = method if method.startswith('http') else 'https://api.github.com/%s' % (method)
  # Make some default headers to send
  headers = { 'Authorization': 'token %s' % (api_token) }

  # Handle paging
  response = requests.get(call, headers = headers)
  link = parse_link_header(response.headers.get('link'))

  # If there is another page, add to collection and keep going
  # but if there is a collection add and return, otherwise, just
  # return response
  if link is not None and 'next' in link:
    return make_request(link['next'], params, collected + response.json())
  elif collected is not None and len(collected) > 0:
    return collected + response.json()
  else:
    return response.json()


# Get repo data
def get_repos():
  for a in accounts:
    repos = make_request('users/%s/repos' % (a))
    for repo in repos:
      data = {
        'repo_id': repo['id'],
        'user_id': repo['owner']['id'],
        'user_name': repo['owner']['name'] if 'name' in repo['owner'] else repo['owner']['login'],
        'name': repo['name'],
        'description': repo['description'],
        'is_fork': repo['fork'],
        'url': repo['html_url'],
        'homepage': repo['homepage'],
        'language': repo['language'],
        'stars': repo['stargazers_count'],
        'watchers': repo['watchers_count'],
        'forks': repo['forks_count'],
        'created': dateutil.parser.parse(repo['created_at']),
        # Pushed is time of last commit, while update includes other updates
        # like dsecription updates
        'updated': dateutil.parser.parse(repo['pushed_at'])
      }
      scraperwiki.sqlite.save(['repo_id'], data, 'repos')


# Get users
def get_users():
  for a in accounts:
    user = make_request('users/%s' % (a))

    if 'message' in user and user['message'].lower() == 'not found':
      return

    data = {
      'user_id': user['id'],
      'login': user['login'],
      'name': user['name'] if 'name' in user else user['login'],
      'avatar': user['avatar_url'],
      'bio': user['bio'] if 'bio' in user else None,
      'location': user['location'] if 'location' in user else None,
      'type': user['type'],
      'url': user['html_url'],
      'created': dateutil.parser.parse(user['created_at'])
    }
    scraperwiki.sqlite.save(['user_id'], data, 'users')


# Make index for full text searching
def make_index():
  tables = scraperwiki.sqlite.show_tables()
  if 'repo_index' not in tables:
    scraperwiki.sqlite.execute('CREATE VIRTUAL TABLE repo_index USING fts4(repo_id INT, content)')
    scraperwiki.sqlite.commit()

  # Update content, remove all first
  scraperwiki.sqlite.execute('DELETE FROM repo_index')
  scraperwiki.sqlite.commit()
  scraperwiki.sqlite.execute("INSERT INTO repo_index (repo_id, content) SELECT repo_id, name || ' ' || description || ' ' || language || ' ' || user_name FROM repos")
  scraperwiki.sqlite.commit()
  # Use with SELECT repo_id FROM repo_index WHERE content MATCH 'string'


# Main stuff
get_users()
get_repos()
make_index()
