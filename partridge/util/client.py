from partridge.util.subjects import parse_paper

from multiprocessing import Pool
import cPickle
import zlib

from multiprocessing.managers import BaseManager

class QueueManager(BaseManager):
    pass

if __name__ == "__main__":

    QueueManager.register("qsize")
    QueueManager.register("get_work")
    QueueManager.register("return_result")

    qm = QueueManager(address=("",1234), authkey="icecream")
    qm.connect()


    queue = qm.qsize()

    batch_size = 12

    p = Pool()

    print qm.qsize()._getvalue()

    while qm.qsize()._getvalue() > 0:
        print "Trying to get %d papers" % batch_size

        batch = cPickle.loads(zlib.decompress(qm.get_work(batch_size)._getvalue()))
        
        results = p.map(parse_paper, batch)

        print "Returning results of batch to server"

        zippedlist = zlib.compress(cPickle.dumps(results))

        qm.return_result(zippedlist)




