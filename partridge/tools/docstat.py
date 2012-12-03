#!/usr/bin/env python
'''
Describe documents in terms of coreSC proportions

'''

from xml.dom import minidom
import os
import sys

class DocStat:

    def parse(self, infile):
        '''Parse infile and make some stats for it
        '''

        with open(infile, 'r') as f:
            doc = minidom.parse(f)

        labels = {}
        sentcount = 0
        for s in doc.getElementsByTagName("s"):
            sentcount += 1
            sentType = self.sentstat(s)
           
            if(sentType == ""):
                sentType = "unknown"

            if(labels.has_key(sentType)):
                labels[sentType] += 1
            else:
                labels[sentType] = 1

        print "There are %d sentences in total" % sentcount
        
        for k in labels.keys():
            print "%d sentences are %s" %(labels[k], k)


    def sentstat(self, sentenceElement):
        '''Get the annotation type for the sentence'''
        
        for el in sentenceElement.childNodes:
            
            if( (el.nodeType == el.ELEMENT_NODE) and
                el.localName == "annotationART"):
                return el.getAttribute("type")

if __name__ == "__main__":
    
    if len(sys.argv) > 1 and  os.path.isfile(sys.argv[1]):
        d = DocStat()
        d.parse(sys.argv[1])
    else:
        print "Usage: %s <annotated document>"
