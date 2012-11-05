'''

Take a known, split paper and annotate it using Sapienta remotely

'''
import os
import pycurl
import codecs

from docparser import SciXML
from crf import Tagger
from progressbar import ProgressBar
from xml.dom import minidom



class Annotator(CURLUploader):
    #------------------------------------------------------------------------- 
    def annotate(self, filename, outfilename):

        c = pycurl.Curl()

        #submit the job to be processed
        form = [ ("paper", (pycurl.FORM_FILE, os.path.abspath(filename))) ]

        c.setopt(pycurl.URL, SAPIENTA_URL)
        c.setopt(c.POST, 1)
        c.setopt(c.HTTPPOST, form)
        print "Uploading %s to SAPIENTA" % filename
        self.perform(c)

        if ("http://www.ebi.ac.uk/errors/failure.html" in self.result or
            self.result.strip() == ""):
            print "Could not annotate paper, servers busy..."
            print "Try running the script with -a %s again" % filename
        else:
            print self.result
    #------------------------------------------------------------------------- 

   
