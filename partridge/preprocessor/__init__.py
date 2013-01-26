"""
Daemon that handles paper uploads and processes new data
"""
import logging
import os
import time
import sys
import traceback

from threading import Thread
from multiprocessing import Queue
from Queue import Empty

from partridge.models import db

from partridge.tools.converter import PDFXConverter
from partridge.tools.annotate import RemoteAnnotator
from partridge.tools.split import SentenceSplitter

from fs import FilesystemWatcher

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

    def run(self):
        """This is the main loop for the paper daemon"""
        self.running = True

        self.fsw.start()

        while self.running:
            try:
                paper = self.fsw.paper_queue.get(block=False)
                self.logger.info("Processing %s", paper)
                try:
                    self._process_paper(paper)
                except Exception as e:
                    #get exception information and dump to user
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    self.logger.error("Error processing paper %s: %s",
                        paper,e)
                    
                    for line in traceback.format_tb(exc_tb):
                        self.logger.error(line)

            except Empty:
                self.logger.debug("No work to do.. going back to sleep")
                time.sleep(1)

        # stop the filesystem watcher
        self.fsw.stop()

    def stop(self):
        self.running = False

    def _process_paper(self, papername):
        """Single method for handling a paper"""

        # set up a list of files that need moving to the processed folder
        # and recording in the db
        paper_files = [ (papername, 'move'),  ]

        basename = os.path.basename(papername)

        name,ext = os.path.splitext(basename)

        infile = papername

        #carry out pdf conversion if necessary
        if( papername.endswith("pdf")):
            infile = self.convertPDF(infile)
        else:
            self.logger.debug("No conversion necessary on file %s", papername)

        #run XML splitting and annotating
        infile = self.splitXML(infile)

        #run XML annotation
        infile = self.annotateXML(infile)

        #Finally do some analysis and store the paper in the DB

    def storePaperData(self, infile):
        """Call the metadata parser and return DB id for this paper"""
        
    
    def annotateXML(self, infile):
        """Routine to start the SAPIENTA process call"""
        
        outfile = os.path.join(self.outdir,  name + "_final.xml")
        
        self.logger.info("Annotating paper %s", infile)

        a = RemoteAnnotator()
        a.annotate( infile, outfile )
        paper_files.append( (outfile, 'store') )

        return outfile


    def splitXML(self, infile):
        """Routine for starting XML splitter call"""

        self.logger.info("Splitting sentences in %s",  infile)
        
        outfile = os.path.join(self.outdir,  name + "_split.xml")

        s = SentenceSplitter()
        s.split(infile, outfile)
        paper_files.append( (outfile, 'delete') )

        return outfile


    def convertPDF(self, infile):
        """Small routine for starting the PDF conversion call
        """

        self.logger.info("Converting %s to xml", infile)

        p = PDFXConverter()
        outfile = os.path.join(self.outdir, name + ".xml")
        p.convert(infile, outfile)

        paper_files.append( (outfile, 'move') )

        return outfile

        


    def cleanup_files(self, papers_list):
        """Move or delete all files involved in the conversion"""

        for filename, action in papers_list:
            
            if action == "move":
                basename = os.path.basename(filename)
                destname = os.path.join(self.outdir, basename)
                os.rename(basename, destname)
            
            elif action == "delete":
              os.delete( filename )

            else:
               #store file in database
               pass


    
#-----------------------------------------------------------------------------

def create_daemon( config ):
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    pdaemon = PaperDaemon(config['PAPER_UPLOAD_DIR'],
            config['PAPER_PROC_DIR'],
            logger)

    return pdaemon

