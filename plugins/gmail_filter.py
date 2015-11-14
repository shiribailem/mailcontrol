"""
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
"""

from sqlalchemy import Table, Column, Integer, String, Boolean, Index
import __filter

class mailfilter(__filter.mailfilter):
    def __init__(self,handle, log, dbsession, dbmeta, **options):
        self.loghandler = log

        self.dbsession = dbsession
        self.dbmeta = dbmeta

        self.gmail_filter = Table('gmail_filter', self.dbmeta,
                                 Column('id', Integer, primary_key=True, autoincrement=True),
                                 Column('tag', String(255), index=True),
                                 Column('seen', Boolean, default=False),
                                 Column('folder', String(255), index=True),
                                 )

    def prepare(self, handle):
        if not handle.folder_exists("Gmail Tags"):
            handle.create_folder("Gmail Tags")

        results = self.dbsession.query(self.gmail_filter).distinct().values(self.gmail_filter.c.folder)

        for result in results:
            if not handle.folder_exists(result.folder):
                handle.create_folder(result.folder)

    def filter(self, handler, id, header):
        addresses = header['To'].lower().split(',')

        for address in addresses:
            if '+' in address:
                tag = address.split("<")[-1].split('+')[1].split('@')[0].lower()

                self.loghandler.output("Found tag: " + tag, 1)

                result = self.dbsession.query(self.gmail_filter).filter_by(tag=tag).first()

                if result:
                    if result.seen:
                        handler.set_flags(id,'\\seen')
                    if not result.folder is None:
                        handler.copy(id,result.folder)
                        handler.delete_messages(id)
                        handler.expunge()
                        return False
                else:
                    if not handler.folder_exists("Gmail Tags." + tag):
                        handler.create_folder("Gmail Tags." + tag)
                    handler.copy(id, "Gmail Tags." + tag)
                    handler.delete_messages(id)
                    handler.expunge()
                    return False

        return True
