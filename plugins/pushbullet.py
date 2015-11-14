"""
Pushbullet: Send notification of new emails to Pushbullet

Requests module must be installed for this plugin to work.

Requires config section:
'''

    [pushbullet]
    ;REQUIRED: Put your Pushbullet access token in this field
    access_token=abcdef
    ;If set to true, will indiscriminately notify for all emails that reach it
    ;Defaults to True if not present
    notify_all=[True/False]

'''

"""

import __filter
import requests
import json

# TODO: Add database functionality for selective notifications

class mailfilter(__filter.mailfilter):
    def __init__(self,handle, log, config, **options):
        self.loghandler = log

        if not config.has_section('pushbullet') or not config.has_option('pushbullet','access_token'):
            raise Exception("pushbullet", "Missing required config options!")

        self.access_token = config.get('pushbullet','access_token')

        if config.has_option('pushbullet','notify_all'):
            self.notify_all = config.getboolean('pushbullet','notify_all')
        else:
            self.notify_all = True

    def filter(self, handler, id, header):

        notify = self.notify_all

        if notify:
            requests.post('https://api.pushbullet.com/v2/pushes', data=json.dumps(
                {'body': header["From"] + ": " + header['Subject'],
                 'title': 'New Priority Email', 'type': 'note'}),
                          headers={'Access-Token': self.access_token,
                                   'Content-Type': 'application/json'})

        return True
