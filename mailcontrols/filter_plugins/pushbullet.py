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

# TODO: Add Database Table Spec to Docstring

import json
import re
from datetime import datetime

import requests
from sqlalchemy import Table, Column, Integer, String, Index
from sqlalchemy import and_, or_, not_
import sqlalchemy.sql as sql

from mailcontrols.filter_plugins import __filter


# TODO: Add database functionality for selective notifications

class mailfilter(__filter.mailfilter):
    def __init__(self, handle, log, dbhandle, dbmeta, config, **options):
        self.loghandler = log

        if not config.has_section('pushbullet') or not config.has_option('pushbullet', 'access_token'):
            raise Exception("pushbullet", "Missing required config options!")

        self.access_token = config.get('pushbullet', 'access_token')

        if config.has_option('pushbullet', 'notify_all'):
            self.notify_all = config.getboolean('pushbullet', 'notify_all')
        else:
            self.notify_all = True

        self.dbhandle = dbhandle
        self.dbmeta = dbmeta

        self.push_filter = Table('push_filter', self.dbmeta,
                                 Column('id', Integer, primary_key=True, autoincrement=True),
                                 Column('username', String(255)),
                                 Column('domain', String(255), index=True),
                                 Column('title', String(30), default="New Email"),
                                 Column('subject', String(255)),
                                 __table_args__=(
                                     Index('filter_address', 'username', 'domain'),
                                 )
                                 )

    def __check_rules(self, header, rules):
        for rule in rules:
            if rule.subject:
                if re.search(rule.subject, header["Subject"]):
                    return rule
            else:
                return rule

        return None

    def filter(self, handler, msgid, header):
        basequery = self.push_filter.select().order_by(
                self.push_filter.c.username.desc(),
                self.push_filter.c.subject.desc()
            )

        address = header['From'].split('<')[-1].split('>')[0].strip().lower()
        username, domain = address.split('@')

        if not self.notify_all:
            results = self.dbhandle.execute(basequery.where(
                            and_(
                                self.push_filter.c.username == username,
                                self.push_filter.c.domain == domain,
                                self.push_filter.c.subject != None
                                )
                            )
                        )

            rule = None

            for entry in results:
                if re.search(entry.subject, header["Subject"]):
                    rule = entry

            if rule is None:

                domainparts = domain.split('.')
                for i in range(-(len(domainparts)), 0):
                    testdomain = '.'.join(domainparts[i:len(domainparts)])
                    self.loghandler.output("Testing %s" % testdomain, 10)

                    rule = self.dbhandle.execute(basequery.where(
                            and_(
                                self.push_filter.c.username == username,
                                self.push_filter.c.domain == testdomain,
                                self.push_filter.c.subject == None
                                )
                            )
                        ).first()

                    if rule is not None:
                        break

        if self.notify_all or rule:
            if rule:
                title = rule.title
            else:
                title = "New Email"

            requests.post('https://api.pushbullet.com/v2/pushes', data=json.dumps(
                    {'body': header["From"] + ": " + header['Subject']
                             + " (" + datetime.now().time().isoformat() + ")",
                     'title': title, 'type': 'note'}),
                          headers={'Access-Token': self.access_token,
                                   'Content-Type': 'application/json'})
            self.loghandler.output("Pushed: %s: %s: %s (%s)" % (
                title, header["From"], header["Subject"],
                datetime.now().time().isoformat()
            ), 10)

        self.loghandler.output(
                "Received message id %d, From: %s with Subject: %s" % (
                    msgid, header['From'], header['Subject']), 10)
        return True
