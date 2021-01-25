""" This is the partridge preprocessor daemon
"""

import sys
import logging
import os
import time
import traceback
import tempfile
import shutil
import base64


from xmlrpc.server import SimpleXMLRPCServer

from partridge.preprocessor.fs import FilesystemWatcher

from threading import Thread
from multiprocessing import Queue
from queue import Empty


from partridge.models import db
from partridge.models.doc import PaperFile, PaperWatcher

from partridge.config import config
from partridge.tools.paperstore import PaperParser
from partridge.tools.papertype import PaperClassifier
from partridge.preprocessor.server import _get_uptox_items, \
    store_result, load_pp_stats, save_pp_stats

#from partridge.preprocessor.tweet import tweet_paper

#from sapienta.tools.converter import PDFXConverter

from partridge.preprocessor.notification import inform_watcher, \
    send_error_report, send_success_report
from partridge.preprocessor.common import PreprocessingException


class PaperExistsException(Exception):
    pass


class PaperDaemon(Thread):
    """This system checks, converts and stores
    """

    running = False

    def __init__(self, indir, pdir, outdir, logger):
        Thread.__init__(self)
        self.fsw = FilesystemWatcher(logger)
        self.fsw.watch_directory(indir)
        self.watchdir = indir
        self.pdir = pdir
        self.outdir = outdir
        self.logger = logger
        self.paper_classifier = PaperClassifier()
        self.processq = Queue()
        self.workercount = 0

# ---------------------------------------------------------------------

    def register_worker_pool(self, size):
        self.workercount += size

    def unregister_worker_pool(self, size):
        self.workercount -= size

    def setup_server(self):

        self.logger.info("Establishing queue management server")

        self.qm = SimpleXMLRPCServer((config['PP_LISTEN_ADDRESS'],
                                      config['PP_LISTEN_PORT']),
                                     logRequests=False,
                                     allow_none=True)

        # load preprocessing stats from disk
        self.stats = load_pp_stats(self.outdir)

        self.qm.register_function(lambda: self.processq.qsize(), "qsize")

        self.qm.register_function(lambda x: _get_uptox_items(
            x, self.processq),             "get_work")

        self.qm.register_function(self.register_worker_pool, "register_pool")

        self.qm.register_function(lambda: self.workercount, "poolsize")

        self.qm.register_function(self.unregister_worker_pool,
                                  "unregister_pool")

        self.qm.register_function(lambda: self.stats[0], "average")

        self.qm.register_function(
            lambda x: store_result(x, self.fsw.paper_queue, self.outdir,
                                   self.logger), "return_result")

        self.logger.info("Listening for paper workers on %s:%d auth=%s",
                         config['PP_LISTEN_ADDRESS'], config['PP_LISTEN_PORT'],
                         config['PP_AUTH_KEY'])

        t = Thread(target=lambda: self.qm.serve_forever())
        t.start()

# ---------------------------------------------------------------------

    def run(self):
        self.running = True

        self.setup_server()
        self.fsw.start()

        # enqueue any xml papers in the working directory
        for root, _, files in os.walk(self.pdir):

            for file in files:
                if(file.endswith(".xml")):
                    self.processq.put(os.path.join(root, file))

        self.logger.info(
            "Found %d files in the 'working' dir queued for annotation", self.processq.qsize())

        while self.running:

            self.task_files = []

            try:
                task = self.fsw.paper_queue.get()
            except:
                continue

            try:
                if task[0] == 'STOP':
                    print("Stopping...")
                    break
                elif task[0] == "QUEUE":
                    # Add paper to queue and convert from PDF if required
                    self.logger.info("Checking if %s exists", task[1])
                    try:
                        self.enqueue(task[1])

                    except PaperExistsException:
                        print("Paper Already exists, cleaning up")
                        self.cleanup(task[1])

                elif task[0] == "STORE":
                    try:
                        self.store(task[1])
                    except PaperExistsException:
                        print("Paper Already exists, cleaning up")
                        self.cleanup(task[1].paper)

            except Exception as e:
                # get exception information and dump to user
                exc_type, exc_obj, exc_tb = sys.exc_info()
                self.logger.error("Error processing paper: %s", e)

                for line in traceback.format_tb(exc_tb):
                    self.logger.error(line)

        self.logger.info("Exited main loop. Shutting down...")
        # when we come out of the loop kill the filesystem watcher
        self.logger.info("Shutting down filesystem watcher...")
        self.fsw.stop()
        self.logger.info("Shutting down XML-RPC server...")
        self.qm.shutdown()


# ---------------------------------------------------------------------

    def store(self, result):
        """Once a document has been handled, store it in file"""

        if(isinstance(result, PreprocessingException)):
            self.handleProcessingException(result)
            print(result.files)
        else:
            filename, outfile, timetaken = result

            if(self.paperExists(outfile)):
                inform_watcher(self.logger, filename,
                               exception=PaperExistsException("Paper Already Exists"))

                self.cleanup(filename)
                return None

            # store the paper object in database
            paperObj = self.storePaperData(outfile)

            # add paper classification to database
            paperObj = self.classifyPaper(paperObj)

            filenames = [filename, outfile]

            basename = os.path.basename(filename)
            name, ext = os.path.splitext(basename)
            pdf = os.path.join(self.watchdir, name + ".pdf")

            if os.path.exists(pdf):
                filenames.append(pdf)

            # add the related files to the db
            self.savePaperFiles(filenames, paperObj)

            self.logger.info("Paper has been added successfully")

            try:
                inform_watcher(self.logger, filename, paperObj=paperObj)
            except Exception as e:
                self.logger.warn("Failed to inform watcher about paper"
                                 + " success: %s", e)

            # if config.has_key('TWITTER_ENABLED') and config['TWITTER_ENABLED']:
            #     try:
            #         tweet_paper(paperObj)
            #     except Exception as e:
            #         self.logger.warn("Could not tweet about paper %s", e)

            # finally update stats
            average = self.stats[0]

            total = self.stats[1] + 1

            if(average == 0.0):
                self.stats = (timetaken, total)
            else:
                self.stats = (average + ((timetaken - average)
                                         / self.stats[1]), total)

            # save the preprocessing stats to disk
            save_pp_stats(self.stats, self.outdir)

            return paperObj

# ---------------------------------------------------------------------
    def savePaperFiles(self, filenames, paper):

        for file in filenames:

            dirname = os.path.dirname(file)
            basename = os.path.basename(file)

            final_path = os.path.join(self.outdir, basename)

            self.logger.info("Saving file %s", final_path)

            if(file != final_path):
                os.rename(file, final_path)

            fileObj = PaperFile(path=final_path)
            db.session.add(fileObj)
            paper.files.append(fileObj)

        db.session.commit()

# ---------------------------------------------------------------------

    def handleProcessingException(self, result):
        """Method for handling processing exceptions"""
        # get exception information and dump to user
        self.logger.error("Error processing paper %s: %s",
                          result.paper, result)

        inform_watcher(self.logger, result.paper, exception=result)

        try:
            print(result.files)
            # send the error report
            send_error_report(result, result.traceback,
                              [result.paper])

        except Exception as e:
            self.logger.error("ERROR SENDING EMAIL: %s", e)

        self.cleanup(result.paper)

# ---------------------------------------------------------------------

    def storeFile(self, filename, data):
        """Store file data retrieved from a remote worker"""

        self.logger.info("Results are in for %s, storing to disk...",
                         filename)

        basename = os.path.basename(filename)
        name, ext = os.path.splitext(basename)

        outfile = os.path.join(self.outdir, name+"_final.xml")

        with open(outfile, 'wb') as f:
            f.write(data)

        return outfile


# ---------------------------------------------------------------------

    def cleanup(self, filename):
        """If something went wrong, clean up mess"""

        basename = os.path.basename(filename)
        dirname = os.path.dirname(filename)
        name, ext = os.path.splitext(basename)

        # delete the file
        self.logger.info("Removing file %s", filename)
        os.unlink(filename)

        pdf = os.path.join(self.watchdir, basename) + ".pdf"

        if(os.path.exists(pdf)):
            self.logger.info("Removing PDF file %s", pdf)

            os.unlink(pdf)

# ---------------------------------------------------------------------

    def stop(self):
        self.logger.info("Sending stop command to task queue")
        self.running = False
        self.fsw.paper_queue.put(("STOP",))
        self.join()

# ---------------------------------------------------------------------

    def enqueue(self, file):
        """Check if a file is a PDF and if it is, convert"""

        self.logger.info("Checking format of file %s", file)

        basename = os.path.basename(file)
        name, ext = os.path.splitext(basename)

        # pdf = False

        # if(basename.endswith(".pdf")):

        #     self.logger.info("%s has been converted and re-queued for paper check",
        #                      self.convertPDF(file))

        # else:
        #     if(self.paperExists(file)):
        #         raise PaperExistsException("Paper Already Exists")

        basename = os.path.basename(file)
        newname = os.path.join(self.pdir, basename)
        os.rename(file, newname)

        self.processq.put(newname)

        # enqueue the file to be annotated
        self.logger.info("%s has been enqueued for annotation", basename)


# ---------------------------------------------------------------------

    def paperExists(self, infile):
        """Return true if paper with same authors and title already in db"""
        parser = PaperParser()

        paper = parser.paperExists(infile)

        if paper != None:
            inform_watcher(self.logger, infile, exists=True, paperObj=paper)

        return paper != None

# ---------------------------------------------------------------------

    def classifyPaper(self, paper):
        """Decide what 'type' the paper is - case study, research or review"""

        type = str(self.paper_classifier.classify_paper(paper))
        self.logger.info("Determined paper %s is of type %s", paper.title,
                         type)

        paper.type = type

        return db.session.merge(paper)


# ---------------------------------------------------------------------

    def storePaperData(self, infile):
        """Call the metadata parser and return DB id for this paper"""
        parser = PaperParser()
        paper = parser.storePaper(infile)
        self.logger.info("Added paper '%s' to database", paper.title)
        return paper


# # ---------------------------------------------------------------------

#     def convertPDF(self, infile):
#         """Small routine for starting the PDF conversion call
#         """

#         self.logger.info("Converting %s to xml", infile)

#         p = PDFXConverter()

#         basename = os.path.basename(infile)

#         name, ext = os.path.splitext(basename)

#         outname = os.path.join(self.watchdir, name + ".xml")

#         p.convert(infile, outname)

#         return outname
