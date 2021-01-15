"""Client code that wraps the worker"""

from multiprocessing import Pool
import os
import pickle
import zlib
import tempfile
import sys
import time
import logging
import traceback
import signal
import sys
import threading

from xmlrpc.client import ServerProxy, Binary

from optparse import OptionParser

from multiprocessing import Process

from partridge.preprocessor.common import PreprocessingException
from partridge.preprocessor.worker import PartridgePaperWorker


logger = logging.getLogger(__name__)

def process_paper( incoming):
    
    tstart = time.time()


    filename, data = incoming

    workdir = tempfile.mkdtemp()

    w = PartridgePaperWorker(logger,workdir)

    name = os.path.join(workdir,os.path.basename(filename))

    with open(name, 'wb') as f:
        f.write(data)

    r = None

    try:
        resultfile = w.process(name)

        with open(resultfile,'rb') as f:
            data = f.read()

        r = filename, data

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
        r = p

    finally:
        logger.info("Cleaning up work directory %s", workdir)
        for root,dirs,files in os.walk(workdir):
            for file in files:
                os.unlink(os.path.join(root,file))

            for dir in dirs:
                os.rmdir(os.path.join(root,dir))

        os.rmdir(workdir)

    tend = time.time()

    tdiff = tend - tstart


    logger.info("Took %d seconds to process paper",tdiff) 

    return r, tdiff

def init_worker():
    signal.signal(signal.SIGINT, signal.SIG_IGN)
        


def run_worker(server, port, password="", processes=None, evt=None):
    """This is an infinite looping method for running a worker pool"""

    logger.info("Connecting to %s:%d with password %s", server,int(port),
        password)

    uri = "http://%s:%d/" % (server,int(port))

    logger.info("Connecting to XML-RPC server on '%s'", uri)

    qm = ServerProxy(uri)
    p = Pool(processes=processes, initializer=init_worker)

    logger.info("Starting worker with %d threads", len(p._pool))

    batch_size = len(p._pool) * 2
    
    logger.info("Registering with server")

    qm.register_pool(len(p._pool))

    while not evt.is_set():
        try:
            
            logger.debug("Trying to get %s jobs from %s:%d",
                batch_size,server,int(port))

            batch = pickle.loads(zlib.decompress(
                qm.get_work(batch_size).data))

            if( len(batch) < 1):
                logger.debug("Nothing to do, sleeping")
                time.sleep(1)

            else:
                results = p.map(process_paper, batch)
                zippedlist = zlib.compress(pickle.dumps(results))

                if zippedlist != None:
                    qm.return_result(Binary(zippedlist))
        except KeyboardInterrupt as e:
            logger.warn("Interrupted client")
            break;


    #unregister workers
    qm.unregister_pool(len(p._pool))

    p.terminate()
    p.join()

#--------------------------------------------------------------------------

def create_client( config, pevt ):
    
    #create process that runs the pool (so many threads *shudder*)
    server = config['PP_LISTEN_ADDRESS']
    port   = config['PP_LISTEN_PORT']
    pw     = config['PP_AUTH_KEY']
    proc   = config['PP_WORKERS']

    p = Process(target=lambda: run_worker(server,port,pw,proc,pevt))
    p.start()

    return p

    

#--------------------------------------------------------------------------

def main():

    usage = "usage: %prog [options] <server> <port> <password>"

    parser = OptionParser(usage=usage)

    parser.add_option("-v", "--verbose", action="store_true", dest="verbose",
        help="If set, run the client in verbose mode")

    parser.add_option("-p", "--processes", action="store", dest="processes",
        default=None, help="Number of threads to run, defaults to number of cores on your CPU")


    (options, args) = parser.parse_args()


    if(options.verbose):
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    if(len(args) < 3):
        parser.print_help()
        sys.exit(1)
    else:
        server   = args[0]
        port     = args[1]
        password = args[2] 

    pevt = threading.Event()

    try:
        p = Process(target=lambda:
        run_worker(server,port,password,int(options.processes),pevt))
        p.start()
        while 1:
            input()
    except KeyboardInterrupt:
        pevt.set()

#--------------------------------------------------------------------------

if __name__ == "__main__":
    main()
