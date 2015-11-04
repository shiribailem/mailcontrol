#!/usr/bin/python -u
__author__ = 'tmajibon'

from imapclient import IMAPClient
from email.parser import HeaderParser
import json
import traceback
from datetime import datetime, timedelta
import MySQLdb
import MySQLdb.cursors
import socket

socket.setdefaulttimeout(30)

class DB:
    conn = None

    def __init__(self, host, user, password, database):
        self.host = host
        self.user = user
        self.password = password
        self.database = database

    def connect(self):
        self.conn = MySQLdb.connect(self.host, self.user, self.password, self.database)
        self.conn.autocommit(True)

    def query(self, sql):
        try:
            cursor = self.conn.cursor()
            resultcount = cursor.execute(sql)
        except (AttributeError, MySQLdb.OperationalError):
            self.connect()
            cursor = self.conn.cursor()
            resultcount = cursor.execute(sql)
        return resultcount, cursor

    def dictquery(self, sql):
        try:
            cursor = self.conn.cursor(MySQLdb.cursors.DictCursor)
            resultcount = cursor.execute(sql)
        except (AttributeError, MySQLdb.OperationalError):
            self.connect()
            cursor = self.conn.cursor()
            resultcount = cursor.execute(sql)
        return resultcount, cursor

class logs:
    def __init__(self, plugin, debug_level=0):
        self.plugin = plugin.upper()
        self.debug = debug_level

    def output(self,msg, debug_level=0):
        if debug_level <= self.debug:
            print("%s %s: %s" %(datetime.now().isoformat(), self.plugin, msg))

def server_login(config):
    server = IMAPClient(config['HOST'], use_uid=True, ssl=config['SSL'])
    server.login(config['USERNAME'],config['PASSWORD'])

    select_info = server.select_folder('INBOX')

    return server


with open('config.json','r') as configfile:
    config = json.loads(configfile.read())

hparser = HeaderParser()

dbhandle = DB(config['database']['host'], config['database']['user'], config['database']['password'], config['database']['database'])
dbhandle.connect()

print("Established Database Connection.")

server = server_login(config)

print("Connected to Server.")

past_emails = server.search()

print("Ignoring emails received prior to program start, %d ignored." %(len(past_emails)))

plugins = []
filters = []

with open('plugins.txt','r') as pluginindex:
    for line in pluginindex.readlines():
        try:
            tempmod = __import__('plugins.' + line.strip(), fromlist=[''])
            plugins.append(tempmod)
            filters.append(tempmod.mailfilter(server, logs(line.strip(), config['debug']), db=dbhandle))
        except:
            logs("PLUGINS",config['debug']).output("Error initializing plugin %s.\n%s" % (line.strip(),traceback.format_exc()),0)

print("%d Plugins Loaded." % (len(plugins)))

print("Beginning primary program loop.")

while True:

    messages = server.search()

    if messages == past_emails:
        try:
            logs('IDLE',config['debug']).output("Entering Idle",5)
            server.idle()
            error = False
            idle_debug = server.idle_check(config['idle_timeout'])
            logs('IDLE',config['debug']).output(idle_debug,5)
            server.idle_done()
        except:
            if config['debug'] > 0:
                logs('IDLE', config['debug']).output(traceback.format_exc(), 1)
            server = server_login(config)
    else:
        logs('IDLE',config['debug']).output("Skipping idle as new activity received during last plugin run.",4)

    error = False

    try:
        logs('SERVER',config['debug']).output("Searching for new emails.", 4)
        messages = server.search()
    except:
        error = True
        logs('SEARCH',config['debug']).output("Error checking message list. Reconnecting Server.", 5)
        try:
            server = server_login(config)
        except:
            print("SERVER: Failed to reconnect. Exiting.")
            break

    if not error:
        for msgid in messages:
            if not msgid in past_emails:
                message = server.fetch(msgid, ['BODY[HEADER]'])
                server.remove_flags(msgid, '\\Seen')

                header = hparser.parsestr(message[msgid]['BODY[HEADER]'])

                for mailfilter in filters:
                    try:
                        if not mailfilter.filter(server, msgid, header):
                            break
                    except:
                        logs('PLUGINS', config['debug']).output("Error Executing plugin.\n" + traceback.format_exc(),1)
        past_emails = messages