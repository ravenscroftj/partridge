#!/usr/bin/python2 

'''
Python tooling for working with annotated XML papers

@author James Ravenscroft
@date 17/12/2012
'''

import sys
import os
import codecs

from pdfminer.pdfparser import PDFParser, PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfdevice import PDFDevice
from pdfminer.layout import LAParams, LTTextBox
from pdfminer.converter import PDFPageAggregator
from pdfminer.pdftypes import resolve1

from xml.dom import minidom

from nltk.tokenize import word_tokenize

class SciXMLConverter(object):

    title = ""

    def convert(self, pdfinput, pdfoutput, pdfpassword=""):
        '''Given a PDF input stream, converts the text to a SciXML document
        '''
        #start the xml stuff
        self.initxml()

            

        self.abstractFound = False

        # initialization routine adapted from PDFMiner documentation
        # http://www.unixuser.org/~euske/python/pdfminer/programming.html
        parser = PDFParser(f)
        doc    = PDFDocument()
        parser.set_document(doc)
        doc.set_parser(parser)
        doc.initialize(pdfpassword)
        
        # Check if the document allows text extraction. If not, abort.
        if not doc.is_extractable:
            raise PDFTextExtractionNotAllowed

        # Create a PDF resource manager object that stores shared resources.
        rsrcmgr = PDFResourceManager()
        # Set parameters for analysis.
        laparams = LAParams()
        # Create a PDF page aggregator object.
        device = PDFPageAggregator(rsrcmgr, laparams=laparams)
        interpreter = PDFPageInterpreter(rsrcmgr, device)

        #Here starts my code for detecting and collecting text regions in the PDF
        for page in doc.get_pages():
            interpreter.process_page(page)
            # receive the LTPage object for the page.
            layout = device.get_result()

            paper_text = ""

            for obj in layout:
                if( isinstance(obj, LTTextBox) ):
                    txt = obj.get_text().replace("\n"," ").replace("  "," ")

                    l = len(word_tokenize(txt))

                    #make some assumptions about the paper title
                    #we can correct these using metadata later (hopefully)
                    if(self.title == ""):
                        self.title = txt

                    if not self.abstractFound:

                        if l > 75:
                            abstract = self.doc.createTextNode(txt)
                            self.abstractEl.appendChild(abstract)
                            self.abstractFound = True
                    else:
                        self.bodyEl.appendChild(self.doc.createTextNode(txt))

        # Get the outlines of the document.
        for xref in doc.xrefs: 
           info_ref = xref.trailer.get('Info') 
           if info_ref: 
                info = resolve1(info_ref)

                if(info.has_key("Title")):
                    self.title = info['Title']
                
                self.titleEl.appendChild(self.doc.createTextNode(self.title))

        #write the XML to the out stream
        self.doc.writexml(pdfoutput)

    def initxml(self):
        self.doc = minidom.Document()

        #set up basic scixml self.doc
        self.paperEl = self.doc.createElement("PAPER")
        self.doc.appendChild(self.paperEl)
        #set up title element
        self.titleEl = self.doc.createElement("TITLE")
        self.paperEl.appendChild(self.titleEl)
        #abstract element
        self.abstractEl = self.doc.createElement("ABSTRACT")
        self.paperEl.appendChild(self.abstractEl)
        #body element
        self.bodyEl = self.doc.createElement("BODY")
        self.paperEl.appendChild(self.bodyEl)
            


if __name__ == "__main__":

    print sys.argv

    if( len(sys.argv) < 2):
        print "Not enough arguments. Try %s <pdffile1> <pdffile2>"
        sys.exit(1)
 
    for infile in sys.argv[1:]:

        print "Converting %s" % infile

        if not(os.path.exists(infile)):
            print "Input file %s does not exist" % infile
            continue
    

        name,ext = os.path.splitext(infile)
        outfile = name + ".xml"

        with open(infile,"rb") as f:
            with codecs.open(outfile,'w', encoding='utf-8') as out:
                s = SciXMLConverter()
                s.convert(f,out, "")

