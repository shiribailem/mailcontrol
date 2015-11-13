class mailfilter:
    def __init__(self,handle, log, **options):
        self.loghandler = log

    def prepare(self, handle):
        pass

    def filter(self, handler, id, header):
        return True
