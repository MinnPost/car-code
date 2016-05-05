#!/usr/bin/env python

import scraperwiki
import requests
import json
import os
from time import sleep
import dateutil.parser
from datetime import datetime
import re

# Get a token. Make sure not to save any tokens here.
api_token = ''
if 'GITHUB_TOKEN' in os.environ:
    api_token = os.environ['GITHUB_TOKEN']

# List of users/orgs that we want to track
accounts = ['minnpost', 'nytimes', 'propublica', 'datadesk', 'texastribune',
    'newsapps', 'nprapps', 'wnyc', 'washingtonpost', 'guardian', 'openNews',
    'documentcloud', 'ajam', 'sourcefabric', 'quartz', 'censusreporter',
    'ireapps', 'datawrapper', 'TheAssociatedPress', 'associatedpress', 'ZeitOnline', 'overview',
    'huffpostdata', 'poderopedia', 'LearningLab', 'glasseyemedia', 'stateimpact',
    'freedomofpress', 'NUKnightLab', 'superdesk', 'nacion', 'cirlabs', 'BBC-News',
    'SCPR', 'PRX', 'vprnet', 'buzzfeednews', 'mcclatchy', 'registerguard',
    'dallasmorningnews', 'voxmedia', 'fivethirtyeight', 'theupshot', 'thunderdome-data',
    'sunlightlabs', 'inn', 'stlpublicradio', 'APMG', 'BBC-News-Labs',
    'ftlabs', 'Financial-Times', 'wraldata', 'theonion', 'jplusplus', 'datanews',
    'tarbell-project', 'newslynx', 'bvisualdata', 'bloomberg', 'seattletimes',
    'newsdev', 'denverpost', 'themarshallproject', 'dowjones', 'InsideEnergy', 'times',
    'buzzfeed-openlab', 'newsappsio', 'lowerquality', 'wireservice']
old_accounts = ['guardianinteractive']



# Check if tables exists
repos_table_exists = True if scraperwiki.sql.select("name FROM sqlite_master WHERE type='table' AND name='repos'") != [] else False
users_table_exists = True if scraperwiki.sql.select("name FROM sqlite_master WHERE type='table' AND name='users'") != [] else False

# Index created
repos_index_created = False

# New users.  This is used to help try to make the made public date a bit
# more accurate
new_users = []


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


# Make index for repos table.
def index_repos():
    index_query = "CREATE INDEX IF NOT EXISTS %s ON repos (%s)"
    scraperwiki.sql.execute(index_query % ('repos_updated', 'updated'))
    scraperwiki.sql.execute(index_query % ('repos_created', 'created'))
    scraperwiki.sql.execute(index_query % ('repos_made_public', 'made_public'))
    scraperwiki.sql.execute(index_query % ('repos_name', 'name'))
    scraperwiki.sql.execute(index_query % ('repos_description', 'description'))
    scraperwiki.sql.execute(index_query % ('repos_is_fork', 'is_fork'))
    scraperwiki.sql.execute(index_query % ('repos_language', 'language'))


# Make a request
def make_request(method, params = {}, collected = []):
    # Allow for simple method call, or for a whole http request
    call = method if method.startswith('http') else 'https://api.github.com/%s' % (method)
    # Make some default headers to send
    headers = { 'Authorization': 'token %s' % (api_token) }

    # Handle paging.  Sleep for a moment so not to run into
    # limits
    response = requests.get(call, headers = headers)
    sleep(3)
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
    global accounts
    global repos_table_exists
    global repos_index_created
    global new_users

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

            # We actually want to know when the repo was "made public",
            # but there is nothing to actually note this, so we guess
            # by marking when we first see it.  But this falls apart if data
            # is start over, like deleting the table, or even if we add a
            # new user.  We try to get around new users by checking for them.
            if repos_table_exists and data['user_name'].lower() not in new_users:
                found_data = scraperwiki.sql.select("* FROM repos WHERE repo_id = '%s'" % (data['repo_id']))
                if found_data == []:
                    data['made_public'] = datetime.utcnow()
                # For old data without made_public, just make the created date
                elif found_data != [] and ('made_public' not in found_data[0] or not found_data[0]['made_public']):
                    data['made_public'] = data['created']
                # If already there
                else:
                    data['made_public'] = dateutil.parser.parse(found_data[0]['made_public'])
            # If the table doesn't exist, use created
            else:
                data['made_public'] = data['created']

            # Save and index if needed
            scraperwiki.sql.save(['repo_id'], data, 'repos')
            repos_table_exists = True

            if not repos_index_created:
                index_repos()
                repos_index_created = True


# Get users
def get_users():
    global accounts
    global users_table_exists
    global new_users

    for a in accounts:
        # Check to see if already in db for the made public date
        if users_table_exists:
            found_data = scraperwiki.sql.select("* FROM users WHERE LOWER(login) = LOWER('%s')" % (a))
            if found_data == []:
                new_users.append(a.lower())

        # Get data from github
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

        scraperwiki.sql.save(['user_id'], data, 'users')
        users_table_exists = True


# Make index for full text searching
def make_index():
    tables = scraperwiki.sql.show_tables()
    if 'repo_index' not in tables:
        scraperwiki.sql.execute('CREATE VIRTUAL TABLE repo_index USING fts4(repo_id INT, content)')
        scraperwiki.sql.commit()

    # Update content, remove all first
    scraperwiki.sql.execute('DELETE FROM repo_index')
    scraperwiki.sql.commit()
    scraperwiki.sql.execute("INSERT INTO repo_index (repo_id, content) SELECT repo_id, name || ' ' || description || ' ' || language || ' ' || user_name FROM repos")
    scraperwiki.sql.commit()
    # Use with SELECT repo_id FROM repo_index WHERE content MATCH 'string'


# Main stuff
get_users()
get_repos()

# The index seems to slow things down significantly
#make_index()
