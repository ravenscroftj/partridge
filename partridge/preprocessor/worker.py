"""Preprocessor worker system for talking to the server
"""
import os
import websockets
import requests
import asyncio
import time

from partridge.models import db
from partridge.models.doc import PaperFile, PaperWatcher

from partridge.tools.paperstore import PaperParser

# from sapienta.tools.converter import PDFXConverter
# from sapienta.tools.annotate import Annotator
# from sapienta.tools.sssplit import SSSplit as SentenceSplitter

#from partridge.tools.papertype import RawPaperClassifier

SAPIENTA_ENDPOINT = "https://sapienta.papro.org.uk"

class PartridgePaperWorker:

    def __init__(self, logger, outdir):
        self.logger = logger
        self.outdir = outdir
        #self.paper_classifier = RawPaperClassifier()


    def process(self, filename):
        basename = os.path.basename(filename)
        name, ext = os.path.splitext(basename)

        infile = filename

        if ext == "pdf":
            outfile = self.name + ".xml"
        else:
            outfile = infile

        self.logger.info("Annotating paper %s", infile)

        r = requests.post(f"{SAPIENTA_ENDPOINT}/submit", files={"file": open(infile,'rb')})

        print(r.json())

        job_id = r.json()['job_id']

        self.logger.info("Polling job status for sapienta job_id=%s", job_id)

        complete = False
        
        while not complete:
            
            self.logger.debug("poll loop for job_id=%s, sleep 5s", job_id)
            time.sleep(5)

            r = requests.post(f"{SAPIENTA_ENDPOINT}/{job_id}/status")

            print(r.json())

            complete = r.json()['annotation_complete']
        
        r = requests.get(f"{SAPIENTA_ENDPOINT}/{job_id}/result")

        with open(outfile, 'w') as f:
            f.write(r.text)

        return outfile

        #classify the paper
        #type = self.classifyPaper(infile)

        # with open(infile,'rb') as f:
        #     data = f.read()

        # return infile
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
