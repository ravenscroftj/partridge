"""
Daemon that handles paper uploads and processes new data
"""
import sys
import logging
import os
import time
import traceback

from threading import Thread
from multiprocessing import Queue
from Queue import Empty

from partridge.preprocessor.fs import FilesystemWatcher
from partridge.preprocessor.notification import send_error_report, \
send_success_report

from partridge.models import db
from partridge.models.doc import PaperFile, PaperWatcher

from partridge.tools.paperstore import PaperParser
from partridge.tools.converter import PDFXConverter
from partridge.tools.annotate import RemoteAnnotator
from partridge.tools.split import SentenceSplitter
from partridge.tools.papertype import PaperClassifier

class PaperExistsException(Exception):
    pass


class PaperDaemon(Thread):
    """The paper daemon handles conversion and preprocessing of papers
    """
    
    running = False

    def __init__(self, watchdir, outdir, logger):
        Thread.__init__(self)
        self.fsw = FilesystemWatcher(logger)
        self.fsw.watch_directory(watchdir)
        self.outdir = outdir
        self.logger = logger
        self.paper_classifier = PaperClassifier()

    def run(self):
        """This is the main loop for the paper daemon"""
        self.running = True

        self.fsw.start()

        while self.running:
            try:
                paper = self.fsw.paper_queue.get(block=False)
                self.logger.info("Processing %s", paper)
                try:
                    paperObj = self._process_paper(paper)

                    self.informWatcher( paper,paperObj=paperObj)

                except Exception as e:
                    #get exception information and dump to user
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    self.logger.error("Error processing paper %s: %s",
                        paper,e)
                    
                    for line in traceback.format_tb(exc_tb):
                        self.logger.error(line)

                    self.informWatcher( paper, 
                        exception=e, 
                        tb=exc_tb,
                        files=[file for file,action in self.paper_files])

                    if not isinstance(e, PaperExistsException):
                    
                        try:
                            #send the error report
                            send_error_report( e, exc_tb, 
                                [file for file,action in self.paper_files])



                        except Exception as e:
                            self.logger.error("ERROR SENDING EMAIL: %s", e)

                    #set paperObj to none for file cleanup
                    paperObj = None

                finally:

                    self.cleanupFiles(paperObj)

            except Empty:
                self.logger.debug("No work to do.. going back to sleep")
                time.sleep(1)

        # stop the filesystem watcher
        self.fsw.stop()

    def informWatcher(self, papername, **kwargs):
        '''Inform watchers of papers what happened to them''' 

        basename = os.path.basename(papername)

        q = PaperWatcher.query.filter(PaperWatcher.filename == basename)

        if(q.count() > 0):
            w = q.first()

            self.logger.info("Informing %s about paper %s", w.email, w.filename) 

            if "paper" in kwargs:
                send_success_report( kwargs['paperObj'], w.email)
            else:
                send_error_report( kwargs['exception'], kwargs['tb'],
                    kwargs['files'], w.email)

            db.session.delete(w)
            db.session.commit()
        

    def stop(self):
        self.running = False

    def _process_paper(self, papername):
        """Single method for handling a paper"""

        # set up a list of files that need moving to the processed folder
        # and recording in the db
        self.paper_files = [ (papername, 'move'),  ]

        basename = os.path.basename(papername)

        self.name,ext= os.path.splitext(basename)

        infile = papername

        #carry out pdf conversion if necessary
        if( papername.endswith("pdf")):
            infile = self.convertPDF(infile)
        else:
            self.logger.debug("No conversion necessary on file %s", papername)

        #see if the paper already exists
        if(self.paperExists(infile)):
            raise PaperExistsException("Paper already exists")

        #run XML splitting and annotating
        infile = self.splitXML(infile)

        #run XML annotation
        infile = self.annotateXML(infile)

        #do some analysis and store the paper in the DB
        paper = self.storePaperData(infile)

        #finally add paper type to the database
        return self.classifyPaper(paper)

    def paperExists(self, infile):
        """Return true if paper with same authors and title already in db"""
        parser = PaperParser()
        return parser.paperExists(infile)

    def storePaperData(self, infile):
        """Call the metadata parser and return DB id for this paper"""
        parser = PaperParser()
        paper = parser.storePaper(infile)
        self.logger.info("Added paper '%s' to database", paper.title)
        return paper

    def classifyPaper(self, paper):
        """Decide what 'type' the paper is - case study, research or review"""
        
        type = str(self.paper_classifier.classify_paper(paper))
        self.logger.info("Determined paper %s is of type %s", paper.title,
            type)

        paper.type = type

        return db.session.merge(paper)
        

    
    def annotateXML(self, infile):
        """Routine to start the SAPIENTA process call"""
        
        outfile = os.path.join(self.outdir,  self.name + "_final.xml")
        
        self.logger.info("Annotating paper %s", infile)

        a = RemoteAnnotator()
        a.annotate( infile, outfile )
        self.paper_files.append( (outfile, 'keep') )

        return outfile


    def splitXML(self, infile):
        """Routine for starting XML splitter call"""

        self.logger.info("Splitting sentences in %s",  infile)
        
        outfile = os.path.join(self.outdir,  self.name + "_split.xml")

        s = SentenceSplitter()
        s.split(infile, outfile)
        self.paper_files.append( (outfile, 'delete') )

        return outfile


    def convertPDF(self, infile):
        """Small routine for starting the PDF conversion call
        """

        self.logger.info("Converting %s to xml", infile)

        p = PDFXConverter()
        outfile = os.path.join(self.outdir, self.name + ".xml")
        p.convert(infile, outfile)

        self.paper_files.append( (outfile, 'keep') )

        return outfile

    def cleanupFiles(self, paper):
        """Move or delete all files involved in the conversion"""

        if(paper == None):
            self.logger.warn("Paper was not processed, removing files")

        def keep_file( filename ):
            fileObj = PaperFile( path=filename )
            db.session.add(fileObj)
            paper.files.append(fileObj)
            db.session.commit()


        for filename, action in self.paper_files:

            if paper == None or action == "delete":
                self.logger.debug("Deleting file %s", filename) 
                os.unlink(filename)

            elif action == "move":
                self.logger.debug("Moving file %s", filename)
                bname = os.path.basename(filename)
                newname = os.path.join(self.outdir, bname)
                os.rename(filename, newname)
                keep_file(newname)

            elif action == "keep":
                self.logger.debug("Keeping file %s", filename)
                keep_file(filename)
    
#-----------------------------------------------------------------------------


