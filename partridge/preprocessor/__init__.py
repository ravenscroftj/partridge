import logging
import os
import time
import sys
import traceback
import dramatiq
import minio

from threading import Thread
from multiprocessing import Queue, Process
from queue import Empty

from partridge.models import db

from dotenv import load_dotenv
from dramatiq.brokers.redis import RedisBroker
from dramatiq.results.backends import RedisBackend
from dramatiq.results import Results

load_dotenv()

redis_broker = RedisBroker(host=os.environ.get("REDIS_HOST", 'localhost'), 
    password=os.environ.get("REDIS_PASSWORD", None))

result_backend = RedisBackend(host=os.environ.get("REDIS_HOST", 'localhost'), 
    password=os.environ.get("REDIS_PASSWORD", None))

redis_broker.add_middleware(Results(backend=result_backend))

dramatiq.set_broker(redis_broker)


def get_minio_client() -> minio.Minio:

    use_ssl = os.environ.get("MINIO_USE_SSL", "1") == '1'

    return minio.Minio(os.environ.get("MINIO_HOST", "localhost:9000"),
        access_key=os.environ.get("MINIO_ACCESS_KEY",""),
        secret_key=os.environ.get("MINIO_SECRET_KEY",""), secure=use_ssl)


def create_daemon( config ):

    from partridge.preprocessor.daemon import PaperDaemon

    """Factory function that sets up a paper daemon given a config object"""   
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    pdaemon = PaperDaemon(config['PAPER_UPLOAD_DIR'], config['PAPER_WORK_DIR'],
        config['PAPER_PROC_DIR'], logger)

    pdaemon.start()

    return pdaemon
