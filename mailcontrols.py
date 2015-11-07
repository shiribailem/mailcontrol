#!/usr/bin/python -u
# ^ -u added as I typically run this using supervisor and it complained about it.

# IMAPClient for obvious reasons.
# email.parser for breaking out email headers into dict objects
# json because I like using that for config files, might change it out for
#     ini at some later time for "user-friendliness"
# traceback to catch errors and give the option to add more info in debug
#     output
# MySQLdb for database connections (of course), will likely later move it to
#     another module when I add a more complex system for database handling
# MySQLdb.cursors just so I can make the dict cursor available in the master
#     object, even though nothing is using it right now
# Socket just to change some socket defaults
from imapclient import IMAPClient
from email.parser import HeaderParser
import json
import traceback
import MySQLdb
import MySQLdb.cursors
import socket

# loghandler object contains background thread and object to handle logging
#     without plugins having to understand or support logging configuration
from mailcontrol.loghandler import logworker, loghandler

# Set a default timeout because some of these server connections can hang.
socket.setdefaulttimeout(30)

# Master object serving as a database handler to wrap up advanced behaviors
# and configurations for use later (especially in plugins).
class DB:
    # default connection object, this should be overwritten almost right away.
    conn = None

    # put config data into object on init, if you can't guess what these
    # options are, then you probably shouldn't be using databases.
    def __init__(self, host, user, password, database):
        self.host = host
        self.user = user
        self.password = password
        self.database = database

    # simple routine to connect to database and make sure database post-connect
    # settings are set.
    def connect(self):
        # connect to database
        self.conn = MySQLdb.connect\
            (self.host, self.user, self.password, self.database)
        # set autocommit as none of the plugins should be writing to the
        # database by default, but other things may be writing to the
        # database elsewhere and we want to read them.
        self.conn.autocommit(True)

    # wrapper for sql queries, returns number of results and cursor
    # object.
    # dictionary true makes the returned cursor object a dictcursor
    def query(self, sql, dictionary=False):
        # First try to get a cursor and perform the query immediately
        try:
            # buffered=True is set as many queries don't need the row results
            # and apparently it can cause errors if you don't get them.
            cursor = self.conn.cursor(dictionary=dictionary, buffered=True)
            resultcount = cursor.execute(sql)
        # on failure, connection likely timed out (because we're not
        # closing them anywhere), reconnect and try again.
        # a second failure is definitely a failure and should be
        # allowed to fail.
        except (AttributeError, MySQLdb.OperationalError):
            self.connect()
            cursor = self.conn.cursor(dictionary=dictionary, buffered=True)
            resultcount = cursor.execute(sql)

        # return the resultcount with the cursor because many queries are only
        # going to be needing to know if there are results without having to
        # collect them.
        return resultcount, cursor

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

logthread = logworker(debug_level=config['debug'])
logthread.start()

with open('plugins.txt','r') as pluginindex:
    for line in pluginindex.readlines():
        try:
            tempmod = __import__('plugins.' + line.strip(), fromlist=[''])
            plugins.append(tempmod)
            filters.append(tempmod.mailfilter(server, loghandler(line.strip(), logqueue=logthread.queue), db=dbhandle))
        except:
            loghandler("PLUGINS",logthread.queue).output("Error initializing plugin %s.\n%s" % (line.strip(),traceback.format_exc()),0)

print("%d Plugins Loaded." % (len(plugins)))

print("Beginning primary program loop.")

while True:

    messages = server.search()

    if messages == past_emails:
        try:
            loghandler('IDLE',logqueue=logthread.queue).output("Entering Idle",5)
            server.idle()
            error = False
            idle_debug = server.idle_check(config['idle_timeout'])
            loghandler('IDLE',logqueue=logthread.queue).output(idle_debug,5)
            server.idle_done()
        except:
            if config['debug'] > 0:
                loghandler('IDLE',logqueue=logthread.queue).output(traceback.format_exc(), 1)
            server = server_login(config)
    else:
        loghandler('IDLE',logqueue=logthread.queue).output("Skipping idle as new activity received during last plugin run.",4)

    error = False

    try:
        loghandler('SERVER',logqueue=logthread.queue).output("Searching for new emails.", 4)
        messages = server.search()
    except:
        error = True
        loghandler('SEARCH',logqueue=logthread.queue).output("Error checking message list. Reconnecting Server.", 5)
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
                        loghandler('PLUGINS',logqueue=logthread.queue).output("Error Executing plugin.\n" + traceback.format_exc(),1)
        past_emails = messages