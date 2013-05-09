"""Preprocessor worker system for talking to the server
"""
import os

from partridge.models import db
from partridge.models.doc import PaperFile, PaperWatcher

from partridge.tools.paperstore import PaperParser
from partridge.tools.converter import PDFXConverter
from partridge.tools.annotate import Annotator
from partridge.tools.split import SentenceSplitter
#from partridge.tools.papertype import RawPaperClassifier

class PartridgePaperWorker:

    def __init__(self, logger, outdir):
        self.logger = logger
        self.outdir = outdir
        self.paper_classifier = RawPaperClassifier()
    
    def process(self, filename):
        basename = os.path.basename(filename)
        self.name,ext = os.path.splitext(basename)

        infile = filename

        #if required, convert to PDF
        if( basename.endswith("pdf")):
            infile = self.convertPDF(infile)
        else:
            self.logger.debug("No conversion necessary on file %s", filename)

        #run XML splitter
        infile = self.splitXML(infile)

        #run XML annotation
        infile = self.annotateXML(infile)

        #classify the paper
        type = self.classifyPaper(infile)

        with open(infile,'rb') as f:
            data = f.read()

        return infile
        #return infile, type

    def annotateXML(self, infile):
        """Routine to start the SAPIENTA process call"""
        
        outfile = os.path.join(self.outdir,  self.name + "_final.xml")
        
        self.logger.info("Annotating paper %s", infile)

        a = Annotator()
        a.annotate( infile, outfile )

        return outfile


    def splitXML(self, infile):
        """Routine for starting XML splitter call"""

        self.logger.info("Splitting sentences in %s",  infile)
        
        outfile = os.path.join(self.outdir,  self.name + "_split.xml")

        s = SentenceSplitter()
        s.split(infile, outfile)

        return outfile

    def convertPDF(self, infile):
        """Small routine for starting the PDF conversion call
        """

        self.logger.info("Converting %s to xml", infile)

        p = PDFXConverter()
        outfile = os.path.join(self.outdir, self.name + ".xml")
        p.convert(infile, outfile)

        return outfile

#    def classifyPaper(self, paper):
#        """Decide what 'type' the paper is - case study, research or review"""
#        
#        type = str(self.paper_classifier.classify_paper(paper))
#        self.logger.info("Determined paper %s is of type %s", paper,
#            type)
#
#        return type
