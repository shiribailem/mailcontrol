__1.1 Unstable__
__2015-11-20__

* Added timestamp to Pushbullet (to clearly identify notifications as different)
* Added command line arguments
    * -1, --once: Skips entering idle and breaks out of the loop after one pass
    * --skip <plugin>: Can be specified multiple times, takes a plugin name.
        Any plugin specified will not load, regardless of whether it is in the 
        plugins.txt file

__1.1 Unstable__
__2015-11-15__

* Added persistence between runs. Now stores previously seen messages
  in inbox_list table to use at the start of next session.
* Added addresses value to [mailcontrol] section of ini to hold list
  of accounts in use (for plugins to match those addresses
* Added Mailinglists plugin

__1.0 Stable__
__2015-11-14__

* Initial Stable Branch Created
* Committed fix for hanging issue (last lingering issue for stable usage)

**Known Issues**

* Currently severely limited options on imap connection 
  (if not using common settings, currently will not connect)
* No interfaces for user to update filters in database without
  resorting to direct SQL queries