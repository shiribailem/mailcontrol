Unknown_domain is a very minimalist filter.

The domain is extract from each email and compared against the known_domains table (only containing one field).

Domains are tested in parts, checking from largest to smallest.

If an email comes in from test@1.example.com:

* example.com will *match*
* 1.example.com will *match*
* 2.example.com will *not match*

Any emails not found in the list will be moved to the "Unknown Domain" folder.

'''


    mysql> describe known_domains;
    +--------+--------------+------+-----+---------+-------+
    | Field  | Type         | Null | Key | Default | Extra |
    +--------+--------------+------+-----+---------+-------+
    | domain | varchar(255) | NO   | PRI | NULL    |       |
    +--------+--------------+------+-----+---------+-------+
    1 row in set (0.01 sec)

'''