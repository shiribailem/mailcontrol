Extremely early version of code. Beginning functionality lacking documentation.

Requires Python MySQL module and imapclient module. (available via pip)

Config files are deprecated, will remove later and likely replace with sqlite functionality 
(after user-friendly update interfaces are created).

Short description of tables (later will add sql templates):

    mysql> show tables;
    
    +-----------------------+
    | Tables_in_mailcontrol |
    +-----------------------+
    | auto_filter           |
    | gmail_filter          |
    | known_domains         |
    +-----------------------+
    3 rows in set (0.00 sec)
    
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
    
    mysql> describe known_domains;
    +--------+--------------+------+-----+---------+-------+
    | Field  | Type         | Null | Key | Default | Extra |
    +--------+--------------+------+-----+---------+-------+
    | domain | varchar(255) | NO   | PRI | NULL    |       |
    +--------+--------------+------+-----+---------+-------+
    1 row in set (0.01 sec)
