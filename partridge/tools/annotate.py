'''

Take a known, split paper and annotate it using Sapienta remotely

'''
import os
import pycurl
import codecs
from urllib import urlencode

from sapienta.docparser import SciXML
from sapienta.crf import Tagger

from progressbar import ProgressBar
from xml.dom import minidom

from partridge.config import config

from curlutil import CURLUploader

from collections import Counter

SAPIENTA_URL="http://www.ebi.ac.uk/Rebholz-srv/sapienta/CoreSCWeb/submitRPC"

MODEL_PATH = str(os.path.join(config.models_dir, "a.model"))

class Annotator:
    #------------------------------------------------------------------------- 
    def annotate(self, filename, outfilename):
        print MODEL_PATH
        tagger = Tagger(MODEL_PATH)
        parser = SciXML()
        doc = parser.parse(filename)
        labels, probabilites = tagger.getSentenceLabelsWithProbabilities(doc)
        
        with open(filename,'r') as fin:
            self.indoc = minidom.parse(filename)

        sentmap = {}

        #get sentences by id
        for s in self.indoc.getElementsByTagName("s"):
            if(s.firstChild.nodeType == self.indoc.ELEMENT_NODE and 
                s.firstChild.localName == "annotationART"):
                
                sentmap[s.getAttribute("sid")] = s.firstChild

        usedTypes = {}

        #modify each valid annotation with correct type
        for key,label in labels:
            if(sentmap.has_key(key)):
                el = sentmap[key]
                el.setAttribute("type", label)

                if not(usedTypes.has_key(label)):
                    usedTypes[label] = 0

                usedTypes[label] += 1

                el.setAttribute("conceptID", label+str(usedTypes[label]))
                
        #write the output document
        print "Writing new xml doc to %s" % outfilename

        with codecs.open(outfilename,'w', encoding='utf-8') as f:
            self.indoc.writexml(f)

    #------------------------------------------------------------------------- 

class RemoteAnnotator(CURLUploader):
    """Class that submits a remote annotation job to sapienta servers and saves
    results
    """

    def __init__(self):
        """"""

    def annotate(self, infile, outfile):
        """Do the actual annotation work"""

        pdata = [('paper', (pycurl.FORM_FILE, infile) )]

        c = pycurl.Curl()
        c.setopt(pycurl.URL, SAPIENTA_URL)
        c.setopt(pycurl.POST,1)
        c.setopt(pycurl.HTTPPOST, pdata)

        print "Uploading %s..." % infile

        self.perform(c)

        tmpnam, sents = self.result.split(":")

        labels = sents.split(">")

        self.__annotateXML(infile, labels, outfile)

    def __annotateXML(self, infile, labels, outfile):
        """Read in the xml document and add labels to it
        """

        with open(infile,"rb") as f:
            doc = minidom.parse(f)


        c = Counter()

        for s in doc.getElementsByTagName("s"):
            if s.parentNode.localName == "article-title": continue 

            label = labels.pop(0)

            c[label] += 1

            annoEl = doc.createElement("CoreSc1")
            annoEl.setAttribute("type", label)
            annoEl.setAttribute("conceptID", label + str(c[label]))
            annoEl.setAttribute("novelty", "None")
            annoEl.setAttribute("advantage","None")

            s.insertBefore(annoEl, s.firstChild)

        with codecs.open(outfile,'w', encoding='utf-8') as f:
            doc.writexml(f)

        

if __name__ == "__main__":
    r = RemoteAnnotator()

    r.annotate("test.xml", "test_output.xml")

