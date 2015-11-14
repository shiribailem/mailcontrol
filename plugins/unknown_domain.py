from sqlalchemy import Table, Column, String
import __filter


class mailfilter(__filter.mailfilter):
    def __init__(self,handle, log, dbsession, dbmeta, **options):
        self.loghandler = log

        self.dbsession = dbsession
        self.dbmeta = dbmeta

        self.known_domains = Table('known_domains', self.dbmeta, Column('domain', String(255), primary_key=True, index=True))

    def prepare(self, handle):
        if not handle.folder_exists("Unknown Domain"):
                handle.create_folder("Unknown Domain")

    def filter(self, handler, id, header):
        if '@' in header['From']:
            domain = header['From'].split('<')[-1].split('>')[0].split('@')[-1].split(' ')[0].strip().lower()

            self.loghandler.output("Checking message from %s" %(domain),4)

            unknown = True

            domainparts = domain.split('.')
            for i in range(-(len(domainparts)),0):
                testdomain = '.'.join(domainparts[i:len(domainparts)])
                self.loghandler.output("Testing %s" %(testdomain),10)

                if self.dbsession.query(self.known_domains).filter(
                                self.known_domains.c.domain == testdomain
                                ).count() > 0:
                    unknown = False
                    break

            if unknown:
                flags = handler.get_flags(id)[id]
                handler.copy(id,'Unknown Domain')

                handler.delete_messages(id)
                handler.expunge()

                self.loghandler.output("%s is unknown, moving." %(domain), 1)


        self.loghandler.output("Received message id %d, From: %s with Subject: %s" %(id, header['From'], header['Subject']),10)
        return True
