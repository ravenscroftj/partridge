from multiprocessing import Queue, Pool, Process
from pyinotify import WatchManager, Notifier, ThreadedNotifier, EventsCodes,ProcessEvent
import logging
import os

class PaperProcesser(ProcessEvent):

    def __init__(self, logger, queue):
        self.logger = logger
        self.queue = queue

    def process_IN_CLOSE_WRITE(self, evt):

        if evt.name.endswith("pdf") or evt.name.endswith("xml"):
            self.logger.info( "Adding %s to queue",
                os.path.join(evt.path,evt.name))
            self.queue.put( ("QUEUE", os.path.join(evt.path,evt.name)) )


class FilesystemWatcher:

    # Mask for FS events we are interested in - currently only care about 
    # writable file streams that have been closed (i.e. a pdf has finished
    # uploading)

    mask = EventsCodes.ALL_FLAGS['IN_CLOSE_WRITE']

    # This is the main watch manager provided by pyinotify
    # we use this to manage subscriptions
    _wm = WatchManager()

    # List of watched directories
    wdd = {}

    # create a thread-safe queue for papers that must be processed.
    paper_queue = Queue()

    def __init__(self, logger):
        self.logger = logger
        self.notifier = ThreadedNotifier(self._wm,
                    PaperProcesser(self.logger,self.paper_queue))


    def watch_directory(self, path):
        """set up threaded directory watcher at given path"""
        
        self._wm.add_watch(path, self.mask, rec=True)

        #add all files in the given directory to queue
        for root,dirs,files in os.walk(path):
            
            for file in files:
                if file.endswith("pdf") or file.endswith("xml"):
                    self.logger.info("Adding %s to queue", file)

                    self.paper_queue.put( ("QUEUE", os.path.join(root,file)) )


    def start(self):
        self.notifier.start()

    def stop(self):
        self.notifier.stop()
