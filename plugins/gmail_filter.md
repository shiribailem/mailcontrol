References gmail_filter table to automatically move emails based on gmail tags.

Tags are specified using a gmail feature that ignores anything after and including a + in the receiving email address.

Example: tmajibon@gmail.com and tmajibon+mailcontrol@gmail.com map to the same address.

In the above example "mailcontrol" is the tag it will search for.

If there is no matching row, tagged emails will be sorted into "Gmail Tags.<tag>" 
(Gmail Tags.mailcontrol in the above example)

Matched tags are processed using the following options.

options:

* seen: Default False. When True the email is marked as seen (or read).
* folder: The folder the email is moved to, with subfolders delimited by periods (.).

'''


    mysql> describe gmail_filter;
    +--------+--------------+------+-----+---------+----------------+
    | Field  | Type         | Null | Key | Default | Extra          |
    +--------+--------------+------+-----+---------+----------------+
    | id     | int(11)      | NO   | PRI | NULL    | auto_increment |
    | tag    | varchar(255) | NO   | MUL | NULL    |                |
    | seen   | tinyint(1)   | YES  |     | 0       |                |
    | folder | varchar(255) | YES  | MUL | NULL    |                |
    +--------+--------------+------+-----+---------+----------------+
    4 rows in set (0.00 sec)
    
'''