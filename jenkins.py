import base64
import configparser
import getpass
import http.client
import json
import os

API = 'api/json'


class JenkinsApi:
    def __init__(self, url, user, token):
        self.conn = http.client.HTTPConnection(url)
        self.auth = self._make_auth(user, token)

    def get(self, path, tries=0):
        self.conn.request('GET', path, headers=self._basic_auth())
        try:
            res = self.conn.getresponse()
        except:
            if tries >= 5:
                raise Exception('Failed to get data from {} after {} attempts'.format(path, tries))
            return self.get(path, tries=tries + 1)
        if res.status != 200:
            raise Exception('Failed to get data from {}'.format(path))
        return res.read().decode('utf-8', errors='ignore')

    def get_json(self, path):
        return json.loads(self.get(path))

    def last_build_number(self, job):
        apiData = self.get_json('{}lastBuild/{}'.format(job['url'], API))
        return int(apiData['number'])

    def get_build_numbers(self, job):
        apiData = self.get_json('{}/{}'.format(job['url'], API))
        return [int(build['number']) for build in apiData['builds']]

    def _make_auth(self, user, token):
        if not user:
            user = getpass.getuser()
        if not token:
            token = getpass.getpass('API Token: ')
        return base64.b64encode(
            '{}:{}'.format(user, token).encode('utf-8')
        ).decode('utf-8')

    def _basic_auth(self):
        return {
            'Authorization': 'Basic {}'.format(self.auth)
        }


def read_api_config():
    confpath = os.path.expanduser('~/.jenkinsapi')
    if os.path.isfile(confpath):
        config = configparser.ConfigParser()
        config.read(confpath)
    else:
        config = {}
    return config


def index_url():
    return '/{}'.format(API)


def job_url(name):
    return '/job/{}/{}'.format(name, API)


def log_url(job, buildnum):
    return '{}{}/consoleText'.format(job['url'], buildnum)


def config_url(job):
    return '{}{}'.format(job['url'], 'config.xml')
