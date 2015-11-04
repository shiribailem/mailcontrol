from datetime import datetime, timedelta
import json

class mailfilter:
    def __init__(self,handle, log, **options):
        self.loghandler = log

        if not "db" in options.keys():
            with open('config/auto_filter.json','r') as file:
                self.config = json.loads(file.read())

            for item in self.config.keys():
                if not handle.folder_exists(item):
                    handle.create_folder(item)
            self.db = None
        else:
            self.db = options['db']

            rcount, cursor = self.db.query("select folder from auto_filter where folder is not null group by folder order by folder")

            results = cursor.fetchall()
            for folder in results:
                if not handle.folder_exists(folder[0]):
                    handle.create_folder(folder[0])

    def filter(self, handler, id, header):
        address = header['From'].split('<')[-1].split('>')[0].strip().lower()
        username, domain = address.split('@')

        if self.db is None:
            for folder in self.config.keys():
                if "domains" in self.config[folder]:
                    for searchdomain in self.config[folder]['domains']:
                        if searchdomain == '.'.join(domain.split('.')[-(searchdomain.count('.') + 1):]):
                            handler.copy(id,folder)
                            handler.delete_messages(id)
                            self.loghandler.output("Filtered message from %s to %s" %(address, folder), 1)
                            handler.expunge()
                            return False
                if "email" in self.config[folder]:
                    for email in self.config['folder']['email']:
                        if email == address:
                            handler.copy(id,folder)
                            handler.delete_messages(id)
                            self.loghandler.output("Filtered message from %s to %s" %(address, folder), 1)
                            handler.expunge()
                            return False
        else:
            rcount, cursor = self.db.query('''select seen, folder from auto_filter where username='%s' and domain='%s' ''' %(username, domain))

            found = False

            if rcount > 0:
                found = True
                seen, folder = cursor.fetchone()
            else:
                domainparts = domain.split('.')
                for i in range(-(len(domainparts)),0):
                    testdomain = '.'.join(domainparts[i:len(domainparts)])
                    self.loghandler.output("Testing %s" %(testdomain),10)
                    rcount, cursor = self.db.query('''select seen, folder from auto_filter where domain='%s' ''' % (testdomain))
                    if rcount > 0:
                        seen, folder = cursor.fetchone()
                        found = True
                        break

            if found:
                if seen:
                    handler.set_flags(id, '\\seen')
                if not folder is None:
                    handler.copy(id, folder)
                    handler.delete_messages(id)
                    self.loghandler.output("Filtered message from %s to %s" %(address, folder), 1)
                    handler.expunge()

                    return False


        self.loghandler.output("Received message id %d, From: %s with Subject: %s" %(id, header['From'], header['Subject']), 10)
        return True
