#!/usr/bin/python2
'''
This script enables the conversion of a PDF document to XML recognised by Sapienta via pdfx

'''
import os
import pycurl
import StringIO

from progressbar import ProgressBar
from optparse import OptionParser
from xml.dom import minidom

PDFX_URL = "http://pdfx.cs.man.ac.uk"

class PDFXConverter:

    def convert(self, filename):

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
       c.setopt(c.NOPROGRESS, 0)
       c.setopt(c.PROGRESSFUNCTION, self.__progress)

       self.result = "" #output from conversion

       c.setopt(pycurl.WRITEFUNCTION, self.__recv)
       self.progress = ProgressBar(pdfsize)
       self.progress.start()
       print "Uploading %s..." % filename
       c.perform()
       self.progress.finish()
       f.close()

       print "Processing resulting XML from %s..." %filename
       self.__processXML()

    def __processXML(self):
        '''Given some input XML, process it and make it sapienta friendly
        '''

        doc = minidom.parseString(self.result)

        print doc

    def __progress(self, download_t, download_d, upload_t, upload_d):
        self.progress.update(upload_d)

    def __recv(self, buf):
        '''Method used to store data received from curl operations
        '''
        self.result += buf
        return len(buf)

if __name__ == "__main__":
    
    usage = "usage: %prog [options] file1.pdf [file2.pdf] "
    
    parser = OptionParser(usage=usage)
    parser.add_option("-s", "--split-sent", action="store_true", dest="split",
        help="If true, split sentences using NLTK sentence splitter")

    (options, args) = parser.parse_args()



    if( len(args) < 1):
        parser.print_help()
        sys.exit(1)
 
    for infile in args:

        print "Converting %s" % infile

        if(options.split):
            print "Splitting sentences in %s" % infile

        if not(os.path.exists(infile)):
            print "Input file %s does not exist" % infile
            continue
    

        name,ext = os.path.splitext(infile)
        outfile = name + ".xml"

        p = PDFXConverter()
        p.convert(infile)
