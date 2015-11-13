from sqlalchemy import Table, Column, Integer, String, Boolean, Index
import json

class mailfilter:
    def __init__(self,handle, log, dbsession, dbmeta, **options):
        self.loghandler = log

        self.dbsession = dbsession
        self.dbmeta = dbmeta

        self.auto_filter = Table('auto_filter', self.dbmeta,
                                 Column('id', Integer, primary_key=True, autoincrement=True),
                                 Column('username', String(255)),
                                 Column('domain', String(255), index=True),
                                 Column('seen', Boolean, default=False),
                                 Column('folder', String(255), index=True),
                                 __table_args__ = (
                                     Index('filter_address', 'username', 'domain'),
                                 )
                                 )



    def prepare(self, handle):
        results = self.dbsession.query(self.auto_filter).distinct().values(self.auto_filter.c.folder)

        for result in results:
            if not handle.folder_exists(result.folder):
                handle.create_folder(result.folder)

    def filter(self, handler, id, header):
        address = header['From'].split('<')[-1].split('>')[0].strip().lower()
        username, domain = address.split('@')

        result = self.dbsession.query(self.auto_filter).filter_by(username=username, domain=domain).first()

        if not result:
            domainparts = domain.split('.')
            for i in range(-(len(domainparts)),0):
                testdomain = '.'.join(domainparts[i:len(domainparts)])
                self.loghandler.output("Testing %s" %(testdomain),10)

                result = self.dbsession.query(self.auto_filter).filter_by(username=None, domain=domain).first()

                if result:
                    break

        if result:
            if result.seen:
                handler.set_flags(id, '\\seen')
            if not result.folder is None:
                handler.copy(id, result.folder)
                handler.delete_messages(id)
                self.loghandler.output("Filtered message from %s to %s" %(address, result.folder), 1)
                handler.expunge()

                return False


        self.loghandler.output("Received message id %d, From: %s with Subject: %s" %(id, header['From'], header['Subject']), 10)
        return True
