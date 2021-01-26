"""Entrypoint for dramatiq worker"""
import dramatiq
import tempfile
import os
from partridge import create_app
from partridge.config import config

app = create_app(config)


from partridge.models import db
from partridge.models.doc import Paper, PaperFile
from partridge.preprocessor import get_minio_client
from partridge.tools.paperstore import PaperParser
from partridge.preprocessor.notification import inform_watcher


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

        basename = os.path.basename(file)

        final_path = os.path.join(config['PAPER_PROC_DIR'], basename)

        logger.info("Saving file %s", final_path)

        if(file != final_path):
            os.rename(file, final_path)

        fileObj = PaperFile(path=final_path)
        db.session.add(fileObj)
        paper.files.append(fileObj)

    db.session.commit()


@dramatiq.actor
def annotate_paper(paper_filename):

    logger = annotate_paper.logger

    from .worker import PartridgePaperWorker

    with tempfile.TemporaryDirectory() as tmpdir:
        worker = PartridgePaperWorker(logger, tmpdir)
        outfile = worker.process(paper_filename)

        logger.info("Created file: %s", outfile)

        pp = PaperParser()
        if pp.paperExists(outfile):

            inform_watcher(logger, paper_filename, exception=PaperExistsException("Paper Already Exists"))

            cleanup.send(logger, paper_filename)
            return

        # store the paper object in database
        paperObj = pp.storePaper(outfile)

        # add paper classification to database
        #paperObj = self.classifyPaper(paperObj)

        
        filenames = [paper_filename, outfile]

        basename = os.path.basename(paper_filename)

        if paper_filename.endswith(".xml") and os.path.exists(paper_filename[:-4] + ".pdf"):
            filenames.append(paper_filename[:-4] + ".pdf")
        

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