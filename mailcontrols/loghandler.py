from __future__ import print_function

import threading
from sys import stderr
from Queue import Queue
from datetime import datetime

class logworker(threading.Thread):
    def __init__(self, debug_level=0, stderr_copy=False, logfile=stderr):
        threading.Thread.__init__(self)

        self.debug = debug_level
        self.logfile = logfile
        self.stderr_copy = stderr_copy

        self.queue = Queue()

        self.daemon = True

    def run(self):
        while True:
            item, plugin, debug_level = self.queue.get()

            if debug_level <= self.debug:
                print(datetime.now().isoformat(), plugin + ": ", item, file=self.logfile)

                if self.stderr_copy:
                    print(datetime.now().isoformat(), plugin + ": ", item, file=stderr)


class loghandler:
    def __init__(self, plugin, logqueue, **args):
        self.plugin = plugin.upper()

        self.queue = logqueue

    def output(self,msg, debug_level=0):
        self.queue.put((msg, self.plugin, debug_level))