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
# Socket just to change some socket defaults
from imapclient import IMAPClient
from email.parser import HeaderParser
import json
import traceback
import MySQLdb
import socket
# loghandler object contains background thread and object to handle logging
#     without plugins having to understand or support logging configuration
from mailcontrol.loghandler import logworker, loghandler

# Set a default timeout because some of these server connections can hang.
socket.setdefaulttimeout(30)


# Master object serving as a database handler to wrap up advanced behaviors
# and configurations for use later (especially in plugins).
# TODO: Move to another module and add ability to select different database
# types (like SQLite)
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
        self.conn = MySQLdb.connect(
            self.host, self.user, self.password, self.database)
        # set autocommit as none of the plugins should be writing to the
        # database by default, but other things may be writing to the
        # database elsewhere and we want to read them.
        self.conn.autocommit(True)

    # wrapper for sql queries, returns number of results and cursor
    # object.
    # dictionary true makes the returned cursor object a dictcursor
    def query(self, sql, dictionary=False):

        # Allow selecting dictionary cursor by setting dictionary to True
        if dictionary:
            cursortype = MySQLdb.cursors.DictCursor
        else:
            cursortype = MySQLdb.cursors.Cursor

        # First try to get a cursor and perform the query immediately
        try:
            cursor = self.conn.cursor(cursortype)
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


# since routine disconnects are expected (due to idle connections) putting
# the connection process into a function so it's easily repeatable.
# returns imapclient object already configured and set to 'INBOX'
def server_login(config):
    server = IMAPClient(config['HOST'], use_uid=True, ssl=config['SSL'])
    server.login(config['USERNAME'], config['PASSWORD'])

    select_info = server.select_folder('INBOX')

    return server


# Load config file into config dictionary
# TODO: change to ini for "user friendliness" and DB config compatibility
with open('config.json', 'r') as configfile:
    config = json.loads(configfile.read())

# create an instance of the header parser, only need one and will re-use it
# times.
hparser = HeaderParser()

# create instance of the DB object that will be used for all database calls
# going forward
# immediately connect to database (if this fails, we really don't want to
# move any further
dbhandle = DB(config['database']['host'], config['database']['user'], config['database']['password'],
              config['database']['database'])
dbhandle.connect()

# basic status info so we know it started
# TODO: add functionality to silence non-debug communications
print("Established Database Connection.")

# log into IMAP and get server handle
server = server_login(config)

print("Connected to Server.")

# Collect email ids already in INBOX, these will be used to check which emails
# are new in the future (if it's not in the list, then it wasn't there last
# time we looked.
past_emails = server.search()

# Basic debug info to identify how many emails were seen on first program run
print("Ignoring emails received prior to program start, %d ignored." % (len(past_emails)))

# empty lists to hold the plugin modules as we parse through them.
# TODO: Add more complexity to store statistics and more elegant handling
plugins = []
filters = []

# Start up the log thread and get the object as we'll need it at this point
# to pass the log queue to each of the plugins
# defaults in class (see mailcontrol.loghandler) will have output go to
# stderr
logthread = logworker(debug_level=config['debug'])
logthread.start()

# parse through the plugins.txt file, each line is just the name of a file in
# the plugins folder
# order matters as the filters in each plugin will be run from top to bottom
# and filters can (intentionally) make the system skip all filters after it
with open('plugins.txt', 'r') as pluginindex:
    for line in pluginindex.readlines():
        try:
            # use __import__ to simply load each plugin as a module, adding it
            # to the plugins list.
            # list isn't technically necessary, but I greatly dislike the idea
            # of loading modules this way without keeping handles
            tempmod = __import__('plugins.' + line.strip(), fromlist=[''])
            plugins.append(tempmod)
            # Create instance of mailfilter that's present in each plugin
            # and put it sequentially in the filters list
            filters.append(tempmod.mailfilter(server, loghandler(line.strip(), logqueue=logthread.queue), db=dbhandle))
        except:
            # If there's a problem with an individual plugin, we want to catch
            # the error and provide output. Debug level 0 as we want to know
            # this regardless.
            # while it's not ideal, we want to be able to continue running even
            # with a failed plugin.
            # will give the plugin name and use traceback to include the
            # exception
            loghandler("PLUGINS", logthread.queue).output(
                "Error initializing plugin %s.\n%s" %
                (line.strip(), traceback.format_exc()), 0)

# Just friendly info confirming the number of plugins
print("%d Plugins Loaded." % (len(plugins)))

# this is just to let the user know we're up and running at this point.
print("Beginning primary program loop.")

# program runs continuously, so just a simple True here.
# any reason for it to stop will just be done with breaks.
while True:

    # At the start of each run check for new emails before entering idle cycle.
    # This is in case new emails arrive while the previous set are being
    # processed.
    messages = server.search()

    # A very simple check, past_emails will always contain the previous list
    # of ids seen. If these don't match, there's new emails since we last
    # looked and we should skip this whole section to process them right away.
    if messages == past_emails:
        # Wrap in try/except because so many of these lines can fail for
        # various connection errors and timeouts.
        # attempt to reconnect if a failure is encountered.
        # will eventually need to collect all the possible exceptions to
        # catch them properly.
        try:
            # Extremely verbose debug info, mostly just so I can track failure
            # locations and watch output to see if it hangs somewhere.
            loghandler('IDLE', logqueue=logthread.queue).output(
                "Entering Idle", 10)

            # put server connection into IDLE state, no active commands can be
            # sent while idle.
            server.idle()
            # block on idle_check, this will block the program until either
            # activity is seen on the server, or the idle_timeout in seconds
            # passed.
            idle_debug = server.idle_check(config['idle_timeout'])

            # More heavily verbose statements, this one just outputs whatever
            # the server sent from idle... will eventually want to actually
            # parse and understand these statements for better efficiency
            loghandler('IDLE', logqueue=logthread.queue).output(idle_debug, 8)

            # End idle status, otherwise code will break on every request sent
            # to server.
            server.idle_done()
        except:
            # something failed in idle... likely a timeout of some sort
            # reconnect and log error
            loghandler('IDLE', logqueue=logthread.queue).output(traceback.format_exc(), 1)
            server = server_login(config)
    else:
        # If we're here, just logging that the check for new emails found
        # something and we're continuing.
        loghandler(
            'IDLE', logqueue=logthread.queue).output(
            "Skipping idle as new activity received during last plugin run.",
            4)

    # Create an error tracker boolean. If true, we'll later skip running the
    # filters.
    error = False

    # Try to grab list of messages, if this fails, try to reconnect to server
    # assuming it was a network disconnect.
    # On failure, set error to True so we know not to try parsing emails this
    # cycle.
    try:
        loghandler('SERVER', logqueue=logthread.queue).output("Searching for new emails.", 4)
        messages = server.search()
    except:
        error = True
        loghandler('SEARCH', logqueue=logthread.queue).output(
            "Error checking message list. Reconnecting Server.", 5)
        try:
            server = server_login(config)
        except:
            # If we can't reconnect, connection is down and we should quit.
            # TODO: add functionality to allow continual retrying
            print("SERVER: Failed to reconnect. Exiting.")
            break

    if not error:
        # Cycle through each msgid to check for new and to pass to filters
        for msgid in messages:
            # If it's in past_emails, then we've seen it before, ignore.
            if msgid not in past_emails:
                # If we're here, it's a new email, grab the headers so we can
                # pass those to the filters.
                message = server.fetch(msgid, ['BODY[HEADER]'])
                # fetching sets the email to seen, remove that flag because
                # we haven't actually looked at it yet.
                # TODO: get flags before hand so that we don't set an email as
                #   unread when it was actually read before us.
                server.remove_flags(msgid, '\\Seen')

                # parse headers into a nice dictionary (thank you email.parser
                # for making this easy!
                header = hparser.parsestr(message[msgid]['BODY[HEADER]'])

                for mailfilter in filters:
                    try:
                        # Run filter function of each plugin.
                        # If the function returns False, this means to stop
                        # running filters on this email.
                        if not mailfilter.filter(server, msgid, header):
                            break
                    except:
                        # If an error is caught in the filter, log it here.
                        # TODO: add info to plugins (see above when adding
                        # them) so this can provide things like the plugin name
                        # and error statistics.
                        loghandler('PLUGINS', logqueue=logthread.queue).output(
                            "Error Executing plugin.\n"
                            + traceback.format_exc(), 1)

        # When done, add list of ids to past_emails list so we know these have
        # all been handled.
        past_emails = messages
