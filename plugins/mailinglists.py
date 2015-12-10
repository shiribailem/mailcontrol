"""
Mailing Lists: Sort emails that didn't specify you in "To"

'''


    mysql> describe mailer_filter;
    +--------+--------------+------+-----+---------+----------------+
    | Field  | Type         | Null | Key | Default | Extra          |
    +--------+--------------+------+-----+---------+----------------+
    | id     | int(11)      | NO   | PRI | NULL    | auto_increment |
    | mailer | varchar(255) | NO   | MUL | NULL    |                |
    | seen   | tinyint(1)   | YES  |     | 0       |                |
    | folder | varchar(255) | YES  | MUL | NULL    |                |
    +--------+--------------+------+-----+---------+----------------+
    4 rows in set (0.00 sec)

'''
"""

from sqlalchemy import Table, Column, Integer, String, Boolean, Index
import __filter

class mailfilter(__filter.mailfilter):
    def __init__(self,handle, log, dbsession, dbmeta, config, **options):
        self.loghandler = log

        self.dbsession = dbsession
        self.dbmeta = dbmeta
        self.addresses = config.get('mailcontrol', 'addresses')

        self.mailer_filter = Table('mailer_filter', self.dbmeta,
                                 Column('id', Integer, primary_key=True, autoincrement=True),
                                 Column('mailer', String(255), index=True),
                                 Column('seen', Boolean, default=False),
                                 Column('folder', String(255), index=True),
                                 Column('priority', Integer, default=0)
                                 )

    def prepare(self, handle):
        if not handle.folder_exists("Mailing Lists"):
            handle.create_folder("Mailing Lists")

        results = self.dbsession.query(self.mailer_filter).distinct().values(self.mailer_filter.c.folder)

        for result in results:
            if not handle.folder_exists(result.folder):
                handle.create_folder(result.folder)

    def filter(self, handler, id, header):
        addresses = header['To'].lower().split(',')
        if header['Cc']:
            addresses.extend(header['Cc'].lower().split(','))
        if header['Bcc']:
            addresses.extend(header['Bcc'].lower().split(','))


        blind_check = True
        clean_addresses = []

        for address in addresses:
            clean_addresses.append(
                address.split("<")[-1].split('>')[0].strip().lower())

        for address in self.addresses:
            if address in clean_addresses:
                blind_check = False

        self.loghandler.output("Received addresses: " + ', '.join(clean_addresses), 10)

        if blind_check:
            rule = self.dbsession.query(self.mailer_filter
                                         ).filter(
                                            self.mailer_filter.c.mailer.in_(clean_addresses)
                                         ).order_by(
                                            self.mailer_filter.c.priority.desc()
                                         ).first()

            if rule is None:
                self.loghandler.output("Defaulting to filter into Mailing Lists.", 5)
                handler.copy(id, 'Mailing Lists')
            else:
                self.loghandler.output(
                    "Rule for %s processing. Seen:%i, Folder:%s" % (
                        rule.mailer, rule.seen, rule.folder)
                    , 5)
                if rule.seen:
                    handler.set_flags(id, '\\seen')
                if not rule.folder is None:
                    handler.copy(id, rule.folder)
                else:
                    self.loghandler.output("No folder specified to filter into Mailing Lists.", 10)
                    handler.copy(id, "Mailing Lists")

            handler.delete_messages(id)
            handler.expunge()

            return False

        return True
