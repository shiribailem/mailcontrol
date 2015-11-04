from datetime import datetime, timedelta
import json

class mailfilter:
    def __init__(self,handle, log, **options):
        self.loghandler = log

        if not handle.folder_exists('Gmail Tags'):
            handle.create_folder('Gmail Tags')

        if not "db" in options.keys():
            with open('config/gmail_tags.json','r') as file:
                self.config = json.loads(file.read())
            self.db = None
        else:
            self.db = options['db']

            rcount, cursor = self.db.query("select folder from gmail_filter where folder is not null group by folder order by folder")

            results = cursor.fetchall()
            for folder in results:
                if not handle.folder_exists(folder[0]):
                    handle.create_folder(folder[0])

    def filter(self, handler, id, header):
        addresses = header['To'].lower().split(',')

        for address in addresses:
            if '+' in address:
                tag = address.split('+')[1].split('@')[0].lower()

                self.loghandler.output("Found tag: " + tag, 1)

                found = False

                if self.db is None:
                    if tag in self.config.keys():
                        found = True
                        if 'read' in self.config[tag].keys() and self.config[tag]['read']:
                            seen = True
                        else:
                            seen = False
                        if 'folder' in self.config[tag].keys():
                            folder = self.config[tag]['folder']
                        else:
                            folder = None
                    else:
                        if not handler.folder_exists("Gmail Tags." + tag):
                            handler.create_folder("Gmail Tags." + tag)
                        handler.copy(id, "Gmail Tags." + tag)

                else:
                    rcount, cursor = self.db.query('''select seen, folder from gmail_filter where tag='%s' ''' % (tag))
                    if rcount > 0:
                        seen, folder = cursor.fetchone()
                        found = True

                if found:
                    if seen:
                        handler.set_flags(id,'\\seen')
                    if not folder is None:
                        handler.copy(id,folder)
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
