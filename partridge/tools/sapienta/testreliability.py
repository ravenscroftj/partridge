from crf import runTagger
import os
import sys

from xml.dom import minidom

PAPER_PATH = "/home/james/tmp/corpus/combined"

total = 0
correct = 0
wrong = 0

for root, dirs, files in os.walk(PAPER_PATH):
    

    for file in files:
    
        sentConcepts = {}

        path = os.path.join(root, file)

        print "Processing file %s " % path

        with open(path,'rb') as f:
            doc = minidom.parse(f)

        for sEl in doc.getElementsByTagName("s"):
            sid = sEl.getAttribute("sid") 

            #now get the coresc
            l = sEl.getElementsByTagName("annotationART")

            if(len(l) < 1):
                l = sEl.getElementsByTagName("CoreSc1")

            if(len(l) > 0):
                concept = l[0].getAttribute("type")

                sentConcepts[ sid ] = concept

        print "Found %d sentences" % len(sentConcepts)
        print "Running tagger"

        #now lets do the tagging and get back each sentence
        labels = runTagger(path)

        for id, type in labels:
            
            if sentConcepts.has_key(id):

                print id
                
                if sentConcepts[id] == type:
                    correct += 1
                else:
                    wrong += 1

                total += 1

        corrpercent = (correct * 100) / total
        wrongpercent = (wrong * 100) / total

        print "Total sentences analysed %d" % total
        print "total correct %d (%d%%)" % (correct, corrpercent)
        print "total wrong %d (%d%%)" % (wrong, wrongpercent)

