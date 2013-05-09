"""
Server daemon for parallel processing papers
"""

import os
import logging
import cPickle
import zlib

from multiprocessing import Queue, Process, log_to_stderr, SUBDEBUG
from multiprocessing.managers import BaseManager


from partridge.config import config
from partridge.preprocessor.result import ResultHandler
from partridge.preprocessor.fs import FilesystemWatcher
from partridge.tools.paperstore import PaperParser
from partridge.tools.converter import PDFXConverter


def _get_uptox_items( x, queue):
    
    work = []
    i=0

    while( (i < x ) & (not queue.empty()) ):
        filename = queue.get()

        p = PaperParser()

        with open(filename,'rb') as f:
            data = f.read()

            i += 1

        work.append( (filename, data) )

    return zlib.compress(cPickle.dumps(work))



class QueueManager(BaseManager):
    pass

def main(watchdir, outdir, logger=logging):

    doneq = Queue()

    fsw = FilesystemWatcher(logger)
    fsw.watch_directory(watchdir)

    QueueManager.register("qsize", lambda:fsw.paper_queue.qsize())

    QueueManager.register("get_work", 
        lambda x: _get_uptox_items(x, fsw.paper_queue, watchdir, outdir, logger))

    QueueManager.register("return_result", 
    lambda x: done_papers(x,doneq, logger) )

    

    qm = QueueManager(address=(config['PP_LISTEN_ADDRESS'],  
    config['PP_LISTEN_PORT']),  authkey=config['PP_AUTH_KEY'])
    
    logger.info("Listening for paper workers on %s:%d auth=%s",
        config['PP_LISTEN_ADDRESS'], config['PP_LISTEN_PORT'],
        config['PP_AUTH_KEY'])

    rh = ResultHandler(outdir, watchdir, doneq, logger)

    logger.info("Starting paper daemon")
    fsw.start()
    qm.start()
    rh.start()
    
    return qm, rh, fsw
