"""System for distributing NLTK work to remote clients
"""

import nltk
import os
import logging
import cPickle
import zlib

from multiprocessing import Queue
from multiprocessing.managers import BaseManager

from partridge.util.subjects import labels, resultdir

from partridge.tools.split import SentenceSplitter

class QueueManager(BaseManager):
    pass

paper_root = "/home/james/dissertation/papers"

def get_uptox_items( x, queue):
    
    work = []
    i=0

    while( (i < x ) & (not queue.empty()) ):
        filename = queue.get()
        dirname = os.path.basename(os.path.dirname(filename))
        label = labels[dirname]
        
        with open(filename,'rb') as f:
            data = zlib.compress(f.read())

        i += 1

        work.append( ( os.path.basename(filename), label, data) )

    return cPickle.dumps(work)


def done_papers( zippedlist ):
        results = cPickle.loads(zlib.decompress(zippedlist))

        for result in results:
            print "Storing results for %s" % result[0]
            with open(os.path.join(resultdir, result[0]), 'wb') as f:
                cPickle.dump(result, f)
                


if __name__ == "__main__":
    
    queue = Queue()
    done = Queue()


    QueueManager.register("qsize", lambda:queue.qsize())
    QueueManager.register("get_work", lambda x: get_uptox_items(x, queue))
    QueueManager.register("return_result", done_papers)
    qm = QueueManager(address=("", 1234), authkey="icecream")


    print "Finding all papers..."

    for root,dirs,files in os.walk(paper_root):

        for file in files:
            if file.endswith("_split.xml"):
                print "Found a paper %s" % file

                if( os.path.exists( os.path.join(resultdir, file))):
                    print "Already have a result for %s. Skipping..." % file
                else:
                    queue.put(os.path.join(root,file))

            elif file.endswith(".xml"):
                print "Found an unsplit paper"

                fname,ext = os.path.splitext(file)

                splitfile = os.path.join(root, fname + "_split" + ext)

                if os.path.exists(splitfile):
                    print "Split file exists for this paper"
                else:
                    s = SentenceSplitter()
                    s.split(os.path.join(root,file), splitfile)
                    queue.put(splitfile)

    print queue.qsize()

    print "Starting server..."

    s = qm.get_server()
    s.serve_forever()
