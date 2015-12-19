"""
Auto Filter: Basic filtering by whole address or domain

References auto_filter table to automatically move emails based on the from address or domain.

Emails are tested first for full match to username@domain before testing only the domain.

Domains are tested in parts, with 1.example.com matching first 1.example.com and then example.com.

In each, rules containing subject matches are checked before rules without subject matches.

(NOTE: Subject field supports regular expressions via the python re package, see
https://docs.python.org/2/library/re.html for information on how to construct for this format.)

First match found is the first applied.

options:

* seen: Default False. When True the email is marked as seen (or read).
* folder: The folder the email is moved to, with subfolders delimited by periods (.).

    mysql> describe auto_filter;
    +----------+------------------+------+-----+---------+----------------+
    | Field    | Type             | Null | Key | Default | Extra          |
    +----------+------------------+------+-----+---------+----------------+
    | id       | int(10) unsigned | NO   | PRI | NULL    | auto_increment |
    | username | varchar(255)     | YES  | MUL | NULL    |                |
    | domain   | varchar(255)     | YES  | MUL | NULL    |                |
    | seen     | tinyint(1)       | YES  |     | 0       |                |
    | folder   | varchar(255)     | YES  | MUL | NULL    |                |
    | subject  | varchar(255)     | YES  |     | NULL    |                |
    +----------+------------------+------+-----+---------+----------------+
    5 rows in set (0.26 sec)

"""

import re
import json

from sqlalchemy import Table, Column, Integer, String, Boolean, Index
from sqlalchemy import insert as sqlinsert
from sqlalchemy import update as sqlupdate
from jinja2 import Template
from pkg_resources import resource_string

from mailcontrols.filter_plugins import __filter


class mailfilter(__filter.mailfilter):
    def __init__(self, handle, log, dbsession, dbmeta, **options):
        self.loghandler = log

        self.dbsession = dbsession
        self.dbmeta = dbmeta

        self.auto_filter = Table('auto_filter', self.dbmeta,
                                 Column('id', Integer, primary_key=True, autoincrement=True),
                                 Column('username', String(255)),
                                 Column('domain', String(255), index=True),
                                 Column('seen', Boolean, default=False),
                                 Column('folder', String(255), index=True),
                                 Column('subject', String(255)),
                                 __table_args__=(
                                     Index('filter_address', 'username', 'domain'),
                                 )
                                 )

    def prepare(self, handle):
        results = self.dbsession.query(self.auto_filter).distinct().values(self.auto_filter.c.folder)

        for result in results:
            if not handle.folder_exists(result.folder):
                handle.create_folder(result.folder)

    def __check_rules(self, header, rules):
        for rule in rules:
            if rule.subject:
                if re.search(rule.subject, header["Subject"]):
                    return rule
            else:
                return rule

        return None

    def filter(self, handler, msgid, header):
        basequery = self.dbsession.query(self.auto_filter). \
            order_by(
                self.auto_filter.c.username.desc(),
                self.auto_filter.c.subject.desc()
        )

        address = header['From'].split('<')[-1].split('>')[0].strip().lower()
        username, domain = address.split('@')

        filter_match = False

        results = basequery.filter_by(username=username, domain=domain).all()

        domainparts = domain.split('.')
        for i in range(-(len(domainparts)), 0):
            testdomain = '.'.join(domainparts[i:len(domainparts)])
            self.loghandler.output("Testing %s" % testdomain, 10)

            results.extend(basequery.filter_by(
                    domain=testdomain,
                    username=None
            ).all())

        result = self.__check_rules(header, results)

        if result:
            if result.seen:
                handler.set_flags(msgid, '\\seen')
            if result.folder is not None:
                handler.copy(msgid, result.folder)
                handler.delete_messages(msgid)
                self.loghandler.output("Filtered message from %s to %s" % (address, result.folder), 1)
                handler.expunge()

                return False

        self.loghandler.output(
                "Received message id %d, From: %s with Subject: %s" % (
                    msgid, header['From'], header['Subject']), 10)
        return True

    def admin(self, params, **options):
        if params.get('function') == '' or params.get('function') is None:
            rules = self.dbsession.query(self.auto_filter).all()

            return Template(
                    resource_string("mailcontrols",
                                    "/webtemplates/auto_filter_index.html.jinja"
                                    )
                    ).render(rules=rules)
        elif params.get('function') == "update":
            data = {
                "username": params.get("username", default=''),
                "domain": params.get("domain", default=''),
                "seen": params.get("seen", default=''),
                "folder": params.get("folder", default=''),
                "subject": params.get("subject", default='')
            }

            if data["domain"].strip() == "":
                return "Domain Required."

            if data["username"] == "":
                data['username'] = None

            if data['seen'] == "on":
                data["seen"] = True
            else:
                data["seen"] = False

            if data["folder"].strip() == "":
                data['folder'] = None

            if data["subject"].strip() == "" or data["subject"] == "None":
                data['subject'] = None

            if params.get("id") == "new":
                self.dbsession.execute(sqlinsert(self.auto_filter).values(data))
            else:
                self.dbsession.execute(sqlupdate(self.auto_filter).values(data).where(self.auto_filter.c.id == params.get("id", type=int)))

            self.dbsession.commit()

            return "Updated.<br/><pre>%s</pre>" % json.dumps(data)