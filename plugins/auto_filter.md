References auto_filter table to automatically move emails based on the from address or domain.

Emails are tested first for full match to username@domain before testing only the domain.

Domains are tested in parts, with 1.example.com matching first 1.example.com and then example.com.

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
    +----------+------------------+------+-----+---------+----------------+
    5 rows in set (0.26 sec)