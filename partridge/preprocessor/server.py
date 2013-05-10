"""
Server daemon for parallel processing papers
"""

import os
import logging
import cPickle
import zlib
from SimpleXMLRPCServer import SimpleXMLRPCServer
from xmlrpclib import Binary

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

    return Binary(zlib.compress(cPickle.dumps(work)))

def store_result(x, queue, outdir, logger):
    
    results = cPickle.loads(zlib.decompress(x.data))

    for result in results:
        if(isinstance(result, Exception)):
            queue.put(("STORE",result))
        else:

            
            basename = os.path.basename(result[0])
            name,ext = os.path.splitext(basename)
            outfile = os.path.join(outdir,name+"_final.xml")

            logger.info("Storing document %s", outfile)
            with open(outfile,'wb') as f:
                f.write(result[1])

            queue.put(("STORE", (result[0], outfile)))
                

