__1.1 Unstable__
__2015-11-15__

* Added persistence between runs. Now stores previously seen messages
  in inbox_list table to use at the start of next session.

__1.0 Stable__
__2015-11-14__

* Initial Stable Branch Created
* Committed fix for hanging issue (last lingering issue for stable usage)

**Known Issues**

* Currently severely limited options on imap connection 
  (if not using common settings, currently will not connect)
* No interfaces for user to update filters in database without
  resorting to direct SQL queries