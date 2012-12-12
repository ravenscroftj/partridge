"""
Daemon that handles paper uploads and processes new data
"""
import logging
import os
import time

from threading import Thread
from multiprocessing import Queue
from Queue import Empty
from fs import FilesystemWatcher

from partridge.models import db

class PaperDaemon(Thread):
    """The paper daemon handles conversion and preprocessing of papers
    """
    
    running = False

    def __init__(self, q, logger):
        Thread.__init__(self)
        self.q = q
        self.logger = logger

    def run(self):
        """This is the main loop for the paper daemon"""
        self.running = True

        while self.running:
            try:
                paper = self.q.get(block=False)
                self.logger.info("Processing %s", paper)
            except Empty:
                self.logger.debug("No work to do.. going back to sleep")
                time.sleep(1)

    def stop(self):
        self.running = False

    def _process_paper(self, papername):
        """Single method for handling a paper"""
        


if __name__ == "__main__":

    running = True

    logging.basicConfig(level=logging.INFO)

    logger = logging.getLogger(__name__)

    fsw = FilesystemWatcher(logger)

    pdaemon = PaperDaemon( fsw.paper_queue, logger)
    
    fsw.start()
    pdaemon.start()

    while running:
        i = raw_input(">>> ")

        if(i.startswith("quit")):
            running = False
            fsw.stop()
            pdaemon.stop()
        elif(i.startswith("watch ")):
            path = i[6:]
            if(os.path.isdir(path)):
                print "Adding %s to watch list" % path
                fsw.watch_directory(path)
            else:
                print "No such directory %s" % path
        else:
            print "unrecognised command"
