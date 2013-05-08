"""
Server daemon for parallel processing papers
"""

import os
import logging
import cPickle
import zlib

from multiprocessing import Queue, Process, log_to_stderr, SUBDEBUG
from multiprocessing.managers import BaseManager

from partridge.preprocessor.result import ResultHandler
from partridge.preprocessor.fs import FilesystemWatcher
from partridge.tools.paperstore import PaperParser
from partridge.tools.converter import PDFXConverter


def _get_uptox_items( x, queue, watchdir, outdir, logger):
    
    work = []
    i=0

    while( (i < x ) & (not queue.empty()) ):
        filename, is_pdf = queue.get()

        p = PaperParser()

        if filename.endswith(".pdf"):
            convert_and_queue(filename, queue, outdir, logger)

        elif p.paperExists(filename):
            logger.warn("Paper %s already exists, removing and purging",
            filename)

            if(is_pdf):
                basename = os.path.basename(filename)
                name,ext = os.path.splitext(basename)
                pdf = os.path.join(watchdir, name + ".pdf")
                logger.warn("Removing PDF File... %s", pdf)

                os.unlink(pdf)

            os.unlink(filename)
        else:
            with open(filename,'rb') as f:
                data = f.read()

            i += 1

            work.append( (filename, data, is_pdf) )

    return zlib.compress(cPickle.dumps(work))

def convert_and_queue(filename, queue, outdir, logger):
    """Convert PDF to XML and save in queue"""

    def pdf_convert():
        basename = os.path.basename(filename)
        name,ext = os.path.splitext(basename)
        outfile = os.path.join(outdir, name + ".xml")

        logger.info("Converting %s to xml", filename)
        p = PDFXConverter()
        p.convert(filename,outfile)

        queue.put((outfile, True))

    p = Process(target=pdf_convert)
    p.start()
    

def done_papers( zippedlist, doneq, logger):
    """When papers have been processed, add them to the DB"""
    results = cPickle.loads(zlib.decompress(zippedlist))
    
    logger.info("Received %d results from worker", len(results))
    for result in results:
        doneq.put(result)


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

    qm = QueueManager(address=("", 1234), authkey="icecream")

    rh = ResultHandler(outdir, watchdir, doneq, logger)

    logger.info("Starting paper daemon")
    fsw.start()
    qm.start()
    rh.start()
    
    return qm, rh, fsw
    
