"""Entrypoint for dramatiq worker"""

import dramatiq
import tempfile
import os
import dotenv
import base64
import pickle
from partridge import create_app
from partridge.config import config

dotenv.load_dotenv()

config.update(os.environ)

app = create_app(config)

from partridge.preprocessor.notification import inform_watcher
from partridge.tools.paperstore import PaperParser
from partridge.preprocessor import get_minio_client
from partridge.models.doc import Paper, PaperFile
from partridge.models import db

class PaperExistsException(Exception):
    pass


@dramatiq.actor
def cleanup(filename):
    """If something went wrong, clean up mess"""

    logger = cleanup.logger

    basename = os.path.basename(filename)
    dirname = os.path.dirname(filename)
    nameroot, _ = os.path.splitext(basename)

    # delete the file
    logger.info("Removing file %s", filename)
    os.unlink(filename)

    pdf = os.path.join(dirname, nameroot) + ".pdf"

    if(os.path.exists(pdf)):
        logger.info("Removing PDF file %s", pdf)
        os.unlink(pdf)


@dramatiq.actor
def savePaperFiles(logger, filenames, paper):

    for file in filenames:

        fileObj = PaperFile(path=file)
        db.session.add(fileObj)
        paper.files.append(fileObj)

    db.session.commit()


@dramatiq.actor
def annotate_paper(paper_filename):

    logger = annotate_paper.logger

    from .worker import PartridgePaperWorker

    mc = get_minio_client()

    with tempfile.TemporaryDirectory() as tmpdir:

        tmpname = os.path.join(tmpdir, os.path.basename(paper_filename))

        mc.fget_object(os.getenv('MINIO_BUCKET'), paper_filename, tmpname)

        worker = PartridgePaperWorker(logger, tmpdir)

        outfile = worker.process(tmpname)

        logger.info("Created file: %s", outfile)

        pp = PaperParser()
        paper = pp.paperExists(outfile)
        if paper is not None:

            inform_watcher.send(paper_filename, exists=True, paper_id=paper.id)

            cleanup.send(paper_filename)
            return

        # store the paper object in database
        paperObj = pp.storePaper(outfile)

        # add paper classification to database
        #paperObj = self.classifyPaper(paperObj)

        nameroot, ext = os.path.splitext(os.path.basename(paper_filename))
        dirname = os.path.dirname(paper_filename)

        final_output = os.path.join(dirname, nameroot + "_annotated.xml")

        mc.fput_object(os.getenv('MINIO_BUCKET'), final_output, outfile)

        filenames = [obj.object_name for obj in mc.list_objects(
            os.getenv('MINIO_BUCKET'), prefix=os.path.join(dirname, nameroot))]

        # add the related files to the db
        savePaperFiles(logger, filenames, paperObj)

        logger.info("Paper has been added successfully")

        try:
            inform_watcher.send(paper_filename, paper_id=paperObj.id)
        except Exception as e:
            logger.warn("Failed to inform watcher about paper"
                        + " success: %s", e)

        # if config.has_key('TWITTER_ENABLED') and config['TWITTER_ENABLED']:
        #     try:
        #         tweet_paper(paperObj)
        #     except Exception as e:
        #         self.logger.warn("Could not tweet about paper %s", e)
