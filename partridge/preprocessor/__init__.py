"""
Daemon that handles paper uploads and processes new data
"""
import logging
import os
import time
import sys

from threading import Thread
from multiprocessing import Queue
from Queue import Empty

from partridge.models import db

from partridge.tools.converter import PDFXConverter
from partridge.tools.annotate import Annotator
from partridge.tools.split import SentenceSplitter

from fs import FilesystemWatcher

class PaperDaemon(Thread):
    """The paper daemon handles conversion and preprocessing of papers
    """
    
    running = False

    def __init__(self, watchdir, outdir, logger):
        Thread.__init__(self)
        self.fsw = FilesystemWatcher(logger)
        self.fsw.watch_directory(watchdir)
        self.outdir = outdir
        self.logger = logger

    def run(self):
        """This is the main loop for the paper daemon"""
        self.running = True

        self.fsw.start()

        while self.running:
            try:
                paper = self.fsw.paper_queue.get(block=False)
                self.logger.info("Processing %s", paper)
                
                name,ext = os.path.splitext(paper)

                if( paper.endswith("pdf")):
                    
                    p = PDFXConverter()
                    outfile = name + ".xml"

            except Empty:
                self.logger.debug("No work to do.. going back to sleep")
                time.sleep(1)

        # stop the filesystem watcher
        self.fsw.stop()

    def stop(self):
        self.running = False

    def _process_paper(self, papername):
        """Single method for handling a paper"""
    
#-----------------------------------------------------------------------------

def create_daemon( config ):
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    pdaemon = PaperDaemon(config['PAPER_UPLOAD_DIR'],
            config['PAPER_PROC_DIR'],
            logger)

    return pdaemon

