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
