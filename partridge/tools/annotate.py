'''

Take a known, split paper and annotate it using Sapienta remotely

'''
import os
import pycurl
import codecs

from sapienta.docparser import SciXML
from sapienta.crf import Tagger

from progressbar import ProgressBar
from xml.dom import minidom



class Annotator:
    #------------------------------------------------------------------------- 
    def annotate(self, filename, outfilename):
        
        tagger = Tagger('a.model')
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

   
