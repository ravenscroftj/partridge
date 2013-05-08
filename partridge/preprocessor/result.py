"""
Handler for preprocessor results sent from a remote worker
"""
import os
import time
import sys
import traceback

from threading import Thread
from Queue import Empty

from partridge.models import db

from partridge.models.doc import PaperFile, PaperWatcher

from partridge.tools.paperstore import PaperParser
from partridge.preprocessor.notification import inform_watcher, \
send_error_report, send_success_report
from partridge.preprocessor.common import PreprocessingException

class ResultHandler(Thread):
    """Store paper results in the database"""

    def __init__(self, outdir, watchdir, queue, logger):
        Thread.__init__(self)
        self.watchdir = watchdir
        self.queue = queue
        self.logger = logger
        self.outdir = outdir

    def stop(self):
        self.running = False

    def _process_paper(self, result):
        
        filename, data, type, ispdf = result

        #if is the result of a PDF conversion, we want to keep the pdf
        if(ispdf):
            name,ext = os.path.splitext(os.path.basename(filename))
            pdf = os.path.join(self.watchdir, name + ".pdf")
            self.logger.info("Keeping PDF file %s", pdf)
            self.paper_files.append( (pdf, 'move'))

        self.paper_files.append( (filename,'move'))

        outfile = self.storeFile(filename, data)
        
        self.paper_files.append( (outfile,'keep') )
        
        #store the paper object in database
        paperObj = self.storePaperData(outfile)

        #add paper classification to database
        paperObj.type = type
        paperObj = db.session.merge(paperObj)

        return paperObj

    def run(self):
        """This is the main event loop for the result handler"""
        self.running = True

        while self.running:
            try:
                self.paper_files = []
                result = self.queue.get(block=False)
                paperObj = None
                
                if(isinstance(result, PreprocessingException)):
                    #get exception information and dump to user
                    self.logger.error("Error processing paper %s: %s",
                        result.paper,result)


                    self.paper_files.append((result.paper,'keep'))


                    if(result.pdf):
                        name,ext = os.path.splitext(os.path.basename(result.paper))
                        pdf = os.path.join(self.watchdir, name + ".pdf")
                        self.paper_files.append( (pdf, 'move'))

                    inform_watcher(self.logger, result.paper, exception=result)
                
                    try:
                        #send the error report
                        send_error_report( e, e.traceback, 
                            e.files)

                    except Exception as e:
                        self.logger.error("ERROR SENDING EMAIL: %s", e)
                else:
                
                    try:
                        paperObj = self._process_paper(result)
                    except Exception as e:

                        exc_type, exc_obj, exc_tb = sys.exc_info()
                        self.logger.error("Error processing paper %s: %s",
                            result[0],e)
                        
                        for line in traceback.format_tb(exc_tb):
                            self.logger.error(line)

                        inform_watcher(self.logger, result[0], exception=e)

                self.cleanupFiles(paperObj)

            except Empty:
                self.logger.debug("No work to do.. going back to sleep")
                time.sleep(1)


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


    def cleanupFiles(self, paper):
        """Move or delete all files involved in the conversion"""

        if(paper == None):
            self.logger.warn("Paper was not processed, removing files")
        else:
            #make sure the paper is bound to the session
            db.session.add(paper)

        def keep_file( filename ):
            fileObj = PaperFile( path=filename )
            db.session.add(fileObj)
            paper.files.append(fileObj)
            db.session.commit()


        for filename, action in self.paper_files:
            
            print self.paper_files

            if paper == None or action == "delete":
                self.logger.debug("Deleting file %s", filename) 
                os.unlink(filename)

            elif action == "move":
                self.logger.debug("Moving file %s", filename)
                bname = os.path.basename(filename)
                newname = os.path.join(self.outdir, bname)

                if(filename != newname):
                    os.rename(filename, newname)

                keep_file(newname)

            elif action == "keep":
                self.logger.debug("Keeping file %s", filename)
                keep_file(filename)

    def storeFile(self, filename, data):
        """Store file data retrieved from a remote worker"""

        self.logger.info("Results are in for %s, storing to disk...",
        filename)

        basename = os.path.basename(filename)
        name,ext = os.path.splitext(basename)

        if(ext == ".pdf"):
            self.logger.info("Keeping PDF file")


            

        outfile = os.path.join(self.outdir, name+"_final.xml")

        with open(outfile,'wb') as f:
            f.write(data)

        return outfile
            



