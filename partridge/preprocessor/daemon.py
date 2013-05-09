""" This is the partridge preprocessor daemon
"""

import sys
import logging
import os
import time
import traceback
import tempfile
import shutil


from partridge.preprocessor.fs import FilesystemWatcher
from threading import Thread
from multiprocessing import Queue
from Queue import Empty


from partridge.models import db
from partridge.models.doc import PaperFile, PaperWatcher

from partridge.config import config
from partridge.tools.paperstore import PaperParser
from partridge.tools.papertype import PaperClassifier
from partridge.preprocessor.server import QueueManager, _get_uptox_items\

from partridge.preprocessor.notification import inform_watcher, \
send_error_report, send_success_report
from partridge.preprocessor.common import PreprocessingException


class PaperDaemon(Thread):
    """This system checks, converts and stores
    """

    running = False

    def __init__(self, indir, pdir, outdir, logger):
        Thread.__init__(self)
        self.fsw = FilesystemWatcher(logger)
        self.fsw.watch_directory(indir)
        self.watchdir = indir
        self.pdir   = pdir
        self.outdir = outdir
        self.logger = logger
        self.paper_classifier = PaperClassifier()
        self.processq = Queue()

#---------------------------------------------------------------------

    def setup_server(self):

        self.logger.info("Establishing queue management server")

        QueueManager.register("qsize", 
            lambda:self.processq.qsize())

        QueueManager.register("get_work", 
            lambda x: _get_uptox_items(x, self.processq, watchdir, outdir, logger))

        QueueManager.register("return_result", 
        lambda x: self.fsw.paper_queue.put( ("STORE",result) ))

        self.qm = QueueManager(address=(config['PP_LISTEN_ADDRESS'],  
            config['PP_LISTEN_PORT']),  authkey=config['PP_AUTH_KEY'])

        self.logger.info("Listening for paper workers on %s:%d auth=%s",
            config['PP_LISTEN_ADDRESS'], config['PP_LISTEN_PORT'],
            config['PP_AUTH_KEY'])

#---------------------------------------------------------------------

    def run(self):
        self.running = True

        self.setup_server()
        self.fsw.start()

        while self.running:
            
            self.task_files = []

            task = self.fsw.paper_queue.get()

            try:
                if task[0] == 'STOP':
                    print "Stopping..."
                    break
                elif task[0] == "QUEUE":
                    #Add paper to queue and convert from PDF if required
                    self.logger.info("Checking if %s exists", task[1])
                    self.enqueue(task[1])

                elif task[0] == "STORE":
                    self.store(task[1])

            except Exception as e:
                print e
                print task[0]

        #when we come out of the loop kill the filesystem watcher
        self.fsw.stop()

#---------------------------------------------------------------------

    def store(self, result):
        """Once a document has been handled, store it in file"""
        
        if(isinstance(result, PreprocessingException)):
            self.handleProcessingException(result)
        else:
            filename, data = result
            self.logger.info("Storing document %s", filename)

            outfile = self.storeFile(filename,data)

            #store the paper object in database
            paperObj = self.storePaperData(outfile)

            #add paper classification to database
            paperObj = self.classifyPaper(paperObj)

            filenames = [filename,outfile]

            basename = os.path.basename(filename)
            name,ext  = os.path.splitext(basename)
            pdf = os.path.join(self.watchdir,name + ".pdf")

            if os.path.exists(pdf):
                filenames.append(pdf)

            #add the related files to the db
            self.savePaperFiles(filenames, paperObj)

            return paperObj

#---------------------------------------------------------------------
    def savePaperFiles(self, filenames, paper):
        

        for file in filenames:
            dirname = os.path.dirname(file)
            basename = os.path.basename(file)


            final_path = os.join(self.outdir,basename)

            if(file != final_path):
                os.rename(file, final_path)

                fileObj = PaperFile(path=final_path)
                db.session.add(fileObj)
                paper.files.append(fileObj)
        
        db.session.commit()

#---------------------------------------------------------------------

    def handleProcessingException(self, result):
        """Method for handling processing exceptions"""
        #get exception information and dump to user
        self.logger.error("Error processing paper %s: %s",
            result.paper,result)


        self.paper_files.append((result.paper,'keep'))

        inform_watcher(self.logger, result.paper, exception=result)
    
        try:
            #send the error report
            send_error_report( e, e.traceback, 
                e.files)

        except Exception as e:
            self.logger.error("ERROR SENDING EMAIL: %s", e)

#---------------------------------------------------------------------
        
    def storeFile(self, filename, data):
        """Store file data retrieved from a remote worker"""

        self.logger.info("Results are in for %s, storing to disk...",
        filename)

        basename = os.path.basename(filename)
        name,ext = os.path.splitext(basename)

        outfile = os.path.join(self.outdir, name+"_final.xml")

        with open(outfile,'wb') as f:
            f.write(data)

        return outfile
            

#---------------------------------------------------------------------

    def cleanup(self, filename):
        """If something went wrong, clean up mess"""

        basename = os.path.basename(filename)
        dirname  = os.path.dirname(filename)
        name,ext = os.path.splitext(basename)

        #delete the file
        self.logger.debug("Removing file %s", filename)

        pdf = os.path.join(self.watchdir, basename)

        if(os.path.exists(pdf)):
            self.logger.debug("Removing PDF file %s", pdf)

#---------------------------------------------------------------------

    def stop(self):
        self.logger.info("Sending stop command to task queue")
        self.fsw.paper_queue.put(("STOP",))
        self.running = False
        self.join()

#---------------------------------------------------------------------

    def enqueue(self, file):
        """Check if a file is a PDF and if it is, convert"""

        self.logger.info("Checking format of file %s", file)

        basename = os.path.basename(file)
        name,ext = os.path.splitext(basename)

        pdf = False

        if(basename.endswith(".pdf")):
            
            self.logger.info("%s has been converted and re-queued for paper check", 
            self.convertPDF(file))


        else:
            if(self.paperExists(file)):
                raise PaperExistsException("Paper Already Exists")

            basename = os.path.basename(file)
            newname = os.path.join(self.pdir, basename)
            os.rename(file, newname)

            self.processq.put(newname)

            #enqueue the file to be annotated
            self.logger.info("%s has been enqueued for annotation", basename)
        

#---------------------------------------------------------------------
        
    def paperExists(self, infile):
        """Return true if paper with same authors and title already in db"""
        parser = PaperParser()
        return parser.paperExists(infile)

#---------------------------------------------------------------------

    def classifyPaper(self, paper):
        """Decide what 'type' the paper is - case study, research or review"""
        
        type = str(self.paper_classifier.classify_paper(paper))
        self.logger.info("Determined paper %s is of type %s", paper.title,
            type)

        paper.type = type

        return db.session.merge(paper)


#---------------------------------------------------------------------

    def storePaperData(self, infile):
        """Call the metadata parser and return DB id for this paper"""
        parser = PaperParser()
        paper = parser.storePaper(infile)
        self.logger.info("Added paper '%s' to database", paper.title)
        return paper


#---------------------------------------------------------------------

    def convertPDF(self, infile):
        """Small routine for starting the PDF conversion call
        """

        self.logger.info("Converting %s to xml", infile)

        p = PDFXConverter()

        name,ext= os.path.splitext(basename)

        outname = os.path.join(self.watchdir,name + ".xml")

        p.convert(infile, outname)

        return outname

#---------------------------------------------------------------------

    def cleanupFiles(self, failed=False):
        """Move or delete all files involved in a queue or store operation"""

        if(failed):
            self.logger.warn("Paper was not processed, removing files")

        for filename, action in self.paper_files:

            if paper == None or action == "delete":
                self.logger.debug("Deleting file %s", filename) 
                os.unlink(filename)

            elif action == "queue":
                self.logger.debug("Moving file %s to queue", filename)

            elif action == "store":
                self.logger.debug("Moving file %s", filename)
                bname = os.path.basename(filename)
                newname = os.path.join(self.outdir, bname)
                os.rename(filename, newname)

            elif action == "keep":
                self.logger.debug("Keeping file %s", filename)
