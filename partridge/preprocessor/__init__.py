import logging
import os
import time
import sys
import traceback

from threading import Thread
from multiprocessing import Queue
from Queue import Empty

from partridge.models import db

from partridge.preprocessor.daemon import PaperDaemon

def create_daemon( config ):
    """Factory function that sets up a paper daemon given a config object"""   
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    pdaemon = PaperDaemon(config['PAPER_UPLOAD_DIR'],
            config['PAPER_PROC_DIR'],
            logger)

    return pdaemon
