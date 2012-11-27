'''
Library for converting PDF to minimal sapienta xml

'''

import os
import pycurl
import codecs

from xml.dom import minidom
from nltk.tokenize import word_tokenize, sent_tokenize

from curlutil import CURLUploader

PDFX_URL = "http://pdfx.cs.man.ac.uk"

class PDFXConverter(CURLUploader):

    nextSID = 1

    #-------------------------------------------------------------------------
    def convert(self, filename, outfile):

       c = pycurl.Curl()

       pdfsize = os.path.getsize(filename)

       header = ["Content-Type: application/pdf", 
            "Content-length: " + str(pdfsize)] 
       
       f = open(filename, 'rb')
       c.setopt(pycurl.URL, PDFX_URL)
       c.setopt(pycurl.HTTPHEADER, header)
       c.setopt(pycurl.FOLLOWLOCATION, True)
       c.setopt(pycurl.POST, 1)
       c.setopt(pycurl.INFILE, f)
       c.setopt(pycurl.INFILESIZE, pdfsize)
       
       print "Uploading %s..." % filename

       self.perform(c, pdfsize)

       f.close()

       print "Saving XML from %s..." %filename
       
       self.indoc = minidom.parseString(self.result)



       print "Writing result to %s" % outfile
       #write resulting xml file
       with codecs.open(outfile,'w', encoding='utf-8') as f:
            self.indoc.writexml(f)
                        
     

    
 
