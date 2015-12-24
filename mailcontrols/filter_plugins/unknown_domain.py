"""
Unknown Domain: Filter emails from unfamiliar domains out of inbox

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
"""

from sqlalchemy import Table, Column, String

from mailcontrols.filter_plugins import __filter


class mailfilter(__filter.mailfilter):
    def __init__(self, handle, log, dbsession, dbmeta, **options):
        self.loghandler = log

        self.dbsession = dbsession
        self.dbmeta = dbmeta

        self.known_domains = Table('known_domains',
                                   self.dbmeta,
                                   Column('domain',
                                          String(255),
                                          primary_key=True,
                                          index=True)
                                   )

    def prepare(self, handle):
        if not handle.folder_exists("Unknown Domain"):
            handle.create_folder("Unknown Domain")

    def filter(self, handler, id, header):
        unknown = True

        if '@' in header['From']:
            domain = header['From'].split('<')[-1].split('>')[0].split('@')[-1].split(' ')[0].strip().lower()

            self.loghandler.output("Checking message from %s" % (domain), 4)

            domainparts = domain.split('.')
            for i in range(-(len(domainparts)), 0):
                testdomain = '.'.join(domainparts[i:len(domainparts)])
                self.loghandler.output("Testing %s" % (testdomain), 10)

                if self.dbsession.query(self.known_domains).filter(
                                self.known_domains.c.domain == testdomain
                ).count() > 0:
                    unknown = False
                    break

        if unknown:
            flags = handler.get_flags(id)[id]
            handler.copy(id, 'Unknown Domain')

            handler.delete_messages(id)
            handler.expunge()

            self.loghandler.output("%s is unknown, moving." % (domain), 1)


        self.loghandler.output(
            "Received message id %d, From: %s with Subject: %s" % (id, header['From'], header['Subject']), 10)
        return True
