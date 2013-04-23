from partridge.util.subjects import parse_paper

from multiprocessing import Pool
import cPickle

from multiprocessing.managers import BaseManager

class QueueManager(BaseManager):
    pass

if __name__ == "__main__":

    QueueManager.register("qsize")
    QueueManager.register("get_work")
    qm = QueueManager(address=("",1234), authkey="icecream")
    qm.connect()


    queue = qm.qsize()

    batch_size = 12

    p = Pool()

    print qm.qsize()._getvalue()

    while qm.qsize() > 0:
        print "Trying to get %d papers" % batch_size

        batch = cPickle.loads(qm.get_work(batch_size)._getvalue())
        
        print len(batch)

        p.map(parse_paper, batch)
