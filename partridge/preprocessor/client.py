"""Client code that wraps the worker"""

from multiprocessing import Pool
import os
import cPickle
import zlib
import tempfile
import sys
import time
import logging
import traceback
import signal
import sys


from multiprocessing.managers import BaseManager

from partridge.preprocessor.common import PreprocessingException
from partridge.preprocessor.worker import PartridgePaperWorker

class QueueManager(BaseManager):
    pass

logger = logging.getLogger(__name__)

def process_paper( incoming):
    
    filename, data, ispdf = incoming

    workdir = tempfile.mkdtemp()

    w = PartridgePaperWorker(logger,workdir)

    name = os.path.join(workdir,os.path.basename(filename))

    with open(name, 'wb') as f:
        f.write(data)

    try:
        resultfile = w.process(name)

        with open(resultfile,'rb') as f:
            data = f.read()

        logger.info("Cleaning up work directory %s", workdir)
        for root,dirs,files in os.walk(workdir):
            for file in files:
                os.unlink(os.path.join(root,file))

            for dir in dirs:
                os.rmdir(os.path.join(root,dir))

        return filename, data, ispdf

    except Exception as e:

        #get exception information and dump to user
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.error("Error processing paper %s: %s",
            filename,e)
        
        for line in traceback.format_tb(exc_tb):
            logger.error(line)

        p = PreprocessingException(e)
        p.traceback = traceback.format_exc()
        p.paper = filename

        for root,dirs,files in os.walk(workdir):
            
            for file in files:
                with open(os.path.join(root,file),'rb') as f:
                    p.files.append( (file, f.read() ) )
        
        return p

def init_worker():
    signal.signal(signal.SIGINT, signal.SIG_IGN)
        

def main():

    usage = "usage: %s <server> <port> <password> [processes]"

    if(len(sys.argv) < 4):
        print usage % sys.argv[0]
        sys.exit()
    else:
        server   = sys.argv[1]
        port     = sys.argv[2]
        password = sys.argv[3] 

    if(len(sys.argv) > 4):
        processes = int(sys.argv[4])
    else:
        processes = None


    QueueManager.register("qsize")
    QueueManager.register("get_work")
    QueueManager.register("return_result")

    logger.info("Connecting to %s:%d with password %s", server,int(port),
        password)

    qm = QueueManager(address=(server,int(port)), authkey=password)
    qm.connect()

    p = Pool(processes=processes, initializer=init_worker)

    logger.info("Starting worker with %d threads", len(p._pool))

    batch_size = len(p._pool) * 2

    running = True
    try:
        while running:
            
            logger.info("Trying to get %s jobs from %s:%d",
                batch_size,server,int(port))

            batch = cPickle.loads(zlib.decompress(
                qm.get_work(batch_size)._getvalue()))

            if( len(batch) < 1):
                logger.debug("Nothing to do, sleeping")
                time.sleep(1)

            else:
                results = p.map(process_paper, batch)
                zippedlist = zlib.compress(cPickle.dumps(results))
                qm.return_result(zippedlist)
    except KeyboardInterrupt:
        print "Shutting down..."
        p.terminate()
        p.join()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)


    main()
