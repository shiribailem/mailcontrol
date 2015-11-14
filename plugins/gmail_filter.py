import json
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
