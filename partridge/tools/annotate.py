'''

Take a known, split paper and annotate it using Sapienta remotely

'''
import sys
import os
import pycurl
import codecs
import subprocess
import tempfile
import logging
from urllib import urlencode

#from sapienta.docparser import SciXML
#from sapienta.crf import Tagger

from partridge.config import config

from progressbar import ProgressBar
from xml.dom import minidom

from partridge.config import config

from curlutil import CURLUploader

from collections import Counter

SAPIENTA_URL="http://www.ebi.ac.uk/Rebholz-srv/sapienta/CoreSCWeb/submitRPC"

MODEL_PATH = str(os.path.join(config['MODELS_DIR'], "a.model"))

class SapientaException(Exception):
    pass


class BaseAnnotator(object):
    """Basic annotator with some boilerplate stuff in it"""

    def _annotateXML(self, labels):
        """Read in the xml document and add labels to it
        """

        c = Counter()

        for s in self.doc.getElementsByTagName("s"):
            if s.parentNode.localName == "article-title": continue 

            label = labels.pop(0)

            c[label] += 1

            annoEl = self.doc.createElement("CoreSc1")
            annoEl.setAttribute("type", label)
            annoEl.setAttribute("conceptID", label + str(c[label]))
            annoEl.setAttribute("novelty", "None")
            annoEl.setAttribute("advantage","None")

            s.insertBefore(annoEl, s.firstChild)


    def __upgradeXML(self):
        """When passed in an old annotation format doc, upgrade the format
        
        This method takes an XML document and replaces old fashioned 
        annotationART style elements with the new CoreSC style.
        """

        for annoEl in self.doc.getElementsByTagName("annotationART"):
            sentEl = annoEl.parentNode

            #remove annotation element from tree
            sentEl.removeChild(annoEl)

            #create the CoreSC element
            coreEl = self.doc.createElement("CoreSc1")


            for key in ['type', 'advantage', 'conceptID', 'novelty']:
                coreEl.setAttribute(key, annoEl.getAttribute(key))

            for child in annoEl.childNodes:
                sentEl.appendChild(child.cloneNode(True))
                child.unlink()

            sentEl.insertBefore( coreEl, sentEl.firstChild)



    def annotate(self, infile, outfile):
        """Do the actual annotation work"""

        #parse doc to see if annotations already present
        with open(infile,"rb") as f:
            self.doc = minidom.parse(f)

        if len(self.doc.getElementsByTagName("annotationART")) > 0:
            self.__upgradeXML()



class LocalPythonAnnotator:
    #------------------------------------------------------------------------- 
    def annotate(self, filename, outfilename):
        """This is still a WIP, need python SAPIENTA first"""
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

class LocalPerlAnnotator(BaseAnnotator):
    """Uses Perl version of sapienta to annotate the given paper"""

    perldir = config['SAPIENTA_PERL_DIR']

    resultdir = config['SAPIENTA_RESULT_DIR']

    def annotate(self,infile,outfile):
        """Start a local instance of Sapienta and annotate the file"""

        #call parent annotation class
        BaseAnnotator.annotate(self,infile,outfile)

        logging.info("Running local Perl annotator using SAPIENTA pipeline")

        #parse doc to see if annotations already present
        if len(self.doc.getElementsByTagName("CoreSc1")) < 1:
            args = ["perl", "pipeline_for_sapient_crfsuite.perl", 
                os.path.abspath(infile)]

            f = tempfile.TemporaryFile()


            logging.info("Calling %s", str(args))
            p = subprocess.Popen(args, cwd=self.perldir, 
                stdout=f, stderr=f)
            logging.info("Waiting for SAPIENTA...")
            p.wait()
            logging.info("SAPIENTA is finished...")

            f.close()

            #now open the results file and recombine
            result = os.path.join(self.resultdir, os.path.basename(infile), "result.txt")

            with open(result,'r') as f:
                labels = f.read().split(">")

            self._annotateXML(labels)

            #delete the result file
            os.unlink(result)

        with codecs.open(outfile,'w', encoding='utf-8') as f:
            self.doc.writexml(f)

                


#------------------------------------------------------------------            

class RemoteAnnotator(BaseAnnotator, CURLUploader):
    """Class that submits a remote annotation job to sapienta servers and saves
    results
    """

    def __init__(self):
        """"""

    def annotate(self, infile, outfile):
        """Do the actual annotation work"""

        BaseAnnotator.annotate(self, infile, outfile)

        #parse doc to see if annotations already present
        if len(self.doc.getElementsByTagName("CoreSc1")) < 1:

            pdata = [('paper', (pycurl.FORM_FILE, infile) )]

            c = pycurl.Curl()
            c.setopt(pycurl.URL, SAPIENTA_URL)
            c.setopt(pycurl.POST,1)
            c.setopt(pycurl.HTTPPOST, pdata)

            logging.info("Uploading %s to annotation server", infile)

            self.perform(c)
            try:
                tmpnam, sents = self.result.split(":")
            except Exception as e:
                raise SapientaException("Empty response from SAPIENTA")

            labels = sents.split(">")

            self._annotateXML( labels )

        with codecs.open(outfile,'w', encoding='utf-8') as f:
            self.doc.writexml(f)






#Set annotator to remote annotator for now
Annotator = LocalPerlAnnotator

if __name__ == "__main__":
    r = Annotator()
    r.annotate("test.xml", "test_output.xml")

