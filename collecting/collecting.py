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
accounts = ['minnpost', 'nytimes', 'propublica', 'datadesk', 'texastribune', 'guardianinteractive', 'newsapps', 'nprapps', 'wnyc']


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
        'repo_id': '%s-%s' % (a.lower(), repo['name'].lower()),
        'user_id': a.lower(),
        'login': repo['owner']['login'],
        'name': repo['name'],
        'description': repo['description'],
        'is_fork': repo['fork'],
        'url': repo['html_url'],
        'homepage': repo['homepage'],
        'language': repo['language'],
        'created': dateutil.parser.parse(repo['created_at']),
        'updated': dateutil.parser.parse(repo['updated_at'])
      }
      scraperwiki.sqlite.save(['repo_id'], data, 'repos')


# Get users
def get_users():
  for a in accounts:
    user = make_request('users/%s' % (a))
    data = {
      'user_id': a.lower(),
      'login': user['login'],
      'name': user['name'],
      'avatar': user['avatar_url'],
      'bio': user['bio'],
      'location': user['location'],
      'type': user['type'],
      'url': user['html_url'],
      'created': dateutil.parser.parse(user['created_at'])
    }
    scraperwiki.sqlite.save(['user_id'], data, 'users')



# Main stuf
get_users()
get_repos()
