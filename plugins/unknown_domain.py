from datetime import datetime, timedelta

class mailfilter:
    def __init__(self,handle, log, **options):
        self.loghandler = log

        self.known_domains = []

        if 'db' in options.keys():
            self.db = options['db']
        else:
            with open('config/unknown_domain.txt','r') as file:
                for line in file.readlines():
                    self.known_domains.append(line.strip())

            if not handle.folder_exists('Unknown Domain'):
                handle.create_folder('Unknown Domain')

            self.db = None


    def filter(self, handler, id, header):
        if '@' in header['From']:
            domain = header['From'].split('<')[-1].split('>')[0].split('@')[-1].split(' ')[0].strip().lower()

            self.loghandler.output("Checking message from %s" %(domain),4)

            unknown = True

            domainparts = domain.split('.')
            for i in range(-(len(domainparts)),0):
                testdomain = '.'.join(domainparts[i:len(domainparts)])
                self.loghandler.output("Testing %s" %(testdomain),10)
                if self.db is None:
                    if testdomain in self.known_domains:
                        unknown = False
                        break
                else:
                    if self.db.query('''select * from known_domains where domain='%s' ''' % (testdomain))[0] > 0:
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
