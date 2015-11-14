#!/usr/bin/python -u
# ^ -u added as I typically run this using supervisor and it complained about it.

# IMAPClient for obvious reasons.
# email.parser for breaking out email headers into dict objects
# json because I like using that for config files, might change it out for
#     ini at some later time for "user-friendliness"
# traceback to catch errors and give the option to add more info in debug
#     output
# Socket just to change some socket defaults
# SQLAlchemy is being used to allow the system to be database agnostic
import sqlalchemy
import sqlalchemy.orm
from imapclient import IMAPClient
from email.parser import HeaderParser
import json
import ConfigParser
import traceback
import socket

# loghandler object contains background thread and object to handle logging
#     without plugins having to understand or support logging configuration
from mailcontrol.loghandler import logworker, loghandler


# Set a default timeout because some of these server connections can hang.
socket.setdefaulttimeout(30)

# since routine disconnects are expected (due to idle connections) putting
# the connection process into a function so it's easily repeatable.
# returns imapclient object already configured and set to 'INBOX'
def server_login(config):
    server = IMAPClient(config.get('imap','host'), use_uid=True, ssl=config.getboolean('imap','ssl'))
    server.login(config.get('imap','username'), config.get('imap','password'))

    select_info = server.select_folder('INBOX')

    return server

# Load Configuration from INI file
config = ConfigParser.RawConfigParser()
config.read('config.ini')

# create an instance of the header parser, only need one and will re-use it
# times.
hparser = HeaderParser()

# Establish and connect to SQLAlchemy Database
dbengine = sqlalchemy.create_engine(config.get('database', 'engine'),
                            pool_recycle=3600)

dbmeta = sqlalchemy.MetaData()
dbsessionmaker = sqlalchemy.orm.sessionmaker(autocommit=True)
dbmeta.bind = dbengine
dbsessionmaker.bind = dbengine

dbengine.connect()

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
logthread = logworker(debug_level=config.getint('mailcontrol','debug'))
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
            filters.append(tempmod.mailfilter(
                server, loghandler(line.strip(), logqueue=logthread.queue),
                dbsession=dbsessionmaker(), dbmeta=dbmeta, config=config))
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

# Create all tables defined in plugins
dbmeta.create_all()
print("Loaded all database tables.")

# Parse every plugin's prepare module to perform any tasks that require tables
# to already exist
for filter in filters:
    filter.prepare(server)

# this is just to let the user know we're up and running at this point.
print("Beginning primary program loop.")

# program runs continuously, so just a simple True here.
# any reason for it to stop will just be done with breaks.
while True:

    # At the start of each run check for new emails before entering idle cycle.
    # This is in case new emails arrive while the previous set are being
    # processed.
    # debug line added to isolate server hangs
    loghandler('SERVER', logqueue=logthread.queue).output(
            "Searching for emails.", 10)
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
            idle_debug = server.idle_check(config.getfloat('imap','idle_timeout'))

            # More heavily verbose statements, this one just outputs whatever
            # the server sent from idle... will eventually want to actually
            # parse and understand these statements for better efficiency
            loghandler('IDLE', logqueue=logthread.queue).output(idle_debug, 8)

            # End idle status, otherwise code will break on every request sent
            # to server.
            server.idle_done()

            # Debug message trying to isolate hangs in the program at likely spots.
            loghandler('IDLE', logqueue=logthread.queue).output("Exited IDLE.", 10)
        except KeyboardInterrupt:
            print("Received Keyboard Interrupt. Exiting.")
            break

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
        loghandler('SERVER', logqueue=logthread.queue).output(
            "Searching for new emails.", 4)
        messages = server.search()
        # Debug message trying to isolate hangs in the program at likely spots.
        loghandler('SERVER', logqueue=logthread.queue).output(
            "Found %i emails total." % (len(messages)), 10)
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
