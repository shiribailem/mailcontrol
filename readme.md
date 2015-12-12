#Mail Control#
__Version 0.2__
__Stable__


Extremely early version of code. Beginning functionality lacking documentation.

Requires sqlalchemy and imapclient. (available via pip)

Uses config.json for configuration, format is standard json (later changing to ini format).

HOST, USERNAME, PASSWORD are the standard imap options
SSL is a boolean, True/False

debug is a verbosity setting, 10 currently being the most verbose.
idle_timeout controls the timeout setting on the idle_check imap function

Database settings are passed to the sqlalchemy connect statement in parts.
Type is the sqlalchemy connector.
Other components are the normal expected options.

No database templates are necessary, plugins load table descriptions in their initialization,
sqlalchemy then creates tables in response.

Plugins are loaded from plugins.txt by filename and filters are applied in the order listed.

Plugins are configured separately, documentation for provided plugins is in plugins folder.
