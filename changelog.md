__0.3 Unstable__
__2015-12-11__

Major Overhaul!

Overhauled entire project for packaging and system deployment

* File references are no longer purely in relation to current directory. Checks the following (in order):
  * current directory
  * ~/.mailcontrols
  * (for filters) /var/lib/mailcontrols/filters
  * /etc/mailcontrols
  * AppData\Roaming\mailcontrols
  * C:\mailcontrols\
  * (for filters) inside site-packages
* Added setup.py (dependencies modeled off of versions currently installed on my system)
* Renamed multiple files to match format
* Moved filter importing login into filter_plugins/__init__
  * Expanded logic to searching multiple locations and loading from deployed egg

__0.2 Stable__
__2015-12-11__

* Added priority field to mailinglists plugin (later intending to add to other filters as well)
* Added timestamp to Pushbullet (to clearly identify notifications as different)
* Added command line arguments
    * -1, --once: Skips entering idle and breaks out of the loop after one pass
    * --skip <plugin>: Can be specified multiple times, takes a plugin name.
        Any plugin specified will not load, regardless of whether it is in the 
        plugins.txt file
* Added persistence between runs. Now stores previously seen messages
  in inbox_list table to use at the start of next session.
* Added addresses value to [mailcontrol] section of ini to hold list
  of accounts in use (for plugins to match those addresses
* Added Mailinglists plugin

__0.1 Stable__
__2015-11-14__

* Initial Stable Branch Created
* Committed fix for hanging issue (last lingering issue for stable usage)

**Known Issues**

* Currently severely limited options on imap connection 
  (if not using common settings, currently will not connect)
* No interfaces for user to update filters in database without
  resorting to direct SQL queries