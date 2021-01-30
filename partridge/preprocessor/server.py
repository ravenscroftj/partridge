"""
Server daemon for parallel processing papers
"""
from __future__ import division

import os
import logging
import pickle
import zlib
import base64

from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.client import Binary

from multiprocessing import Queue, Process, log_to_stderr, SUBDEBUG
from multiprocessing.managers import BaseManager


import logging

from partridge.config import config
from partridge.preprocessor.result import ResultHandler
from partridge.preprocessor.fs import FilesystemWatcher
from partridge.tools.paperstore import PaperParser

from partridge.preprocessor.notification import inform_watcher

_average = 0.0
_totalhandled = 0

logger = logging.getLogger(__name__)

def load_pp_stats(dirname):
    stats = os.path.join(dirname,"stats.pickle")
    try:
        with open(stats,'rb') as f:
            return pickle.load(f)
    except IOError:
        return 0.0,0      

def save_pp_stats(stats, dirname):
    statfile = os.path.join(dirname,"stats.pickle")

    with open(statfile,'wb') as f:
        pickle.dump(stats,f)


def _get_uptox_items( x, queue):
    
    work = []
    i=0

    while( (i < x ) & (not queue.empty()) ):
        filename = queue.get()

        p = PaperParser()

        if filename.endswith('xml'):
            paper = p.paperExists(filename)

            if paper != None:
                logger.info("Paper already exists for %s, skipping...", filename)
                os.unlink(filename)
                inform_watcher(logger, filename, exists=True, paperObj=paper)
                continue


        with open(filename,'rb') as f:
            data = f.read()

            i += 1

        work.append( (filename, data ))


    #print(Binary(zlib.compress(pickle.dumps(work))))

    return zlib.compress(pickle.dumps(work))

def store_result(x, queue, outdir, logger):
    
    results = pickle.loads(zlib.decompress(x.data))

    for result,time in results:

        if(isinstance(result, Exception)):
            queue.put(("STORE",result))
        else:
            basename = os.path.basename(result[0])
            name,ext = os.path.splitext(basename)
            outfile = os.path.join(outdir,name+"_final.xml")

            logger.info("Storing document %s", outfile)
            with open(outfile,'wb') as f:
                f.write(result[1])

            queue.put(("STORE", (result[0], outfile, time)))


