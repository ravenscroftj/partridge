import logging
import os
import time
import sys
import traceback

from threading import Thread
from multiprocessing import Queue, Process
from Queue import Empty

from partridge.models import db

from partridge.preprocessor.server import main as server_main
from partridge.preprocessor.client import main as client_main

def create_daemon( config ):
    """Factory function that sets up a paper daemon given a config object"""   
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    qm,rh,fsw = server_main(config['PAPER_UPLOAD_DIR'],
            config['PAPER_PROC_DIR'],
            logger)

    return qm,rh,fsw
