class mailfilter:
    def __init__(self,handle, log, **options):
        self.loghandler = log

    def filter(self, handler, id, header):
        self.loghandler.output("Received message id %d, From: %s with Subject: %s" %(id, header['From'], header['Subject']),10)
        return True
