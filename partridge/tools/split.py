'''
Module for splitting sentences on articles that need splitting
'''
import codecs
import logging
import cPickle
import os

from nltk.tokenize.punkt import PunktSentenceTokenizer

from xml.dom import minidom
from sets import Set

from partridge.config import config

blacklist = set(['journal-id', 'journal-meta','article-id','article-categories'
'contrib','contrib-group', 'aff','pub-date','volume','issue','elocation-id', 
'history','author-notes', 'copyright-statement',
'copyright-year','counts','s', 'subj-group','author-notes', 'alt-title',
'title','ref-list','ack','meta','permissions', 'custom-meta-group'])

logging.basicConfig(level=logging.DEBUG)

SPLITTER_PATH = str(os.path.join(config['MODELS_DIR'], "splitter.dat"))

class SentenceSplitter:
    '''XML Aware sentence splitter for Partridge
    '''

    def __init__(self):

        with open(SPLITTER_PATH,'rb') as f:
            self.tokenizer = cPickle.load(f)

        #self.tokenizer = PunktSentenceTokenizer()
        self.nextSID = 1

    def split(self, filename, outfile):
        
        #read the document
        with open(filename, 'rb') as f:
            self.indoc = minidom.parse(f)

        logging.debug("Parsed input file %s " % filename)

        # check for existence of multiple s elements, possibly skip
        # actually splitting things
        if(len(self.indoc.getElementsByTagName("s")) > 0):
            logging.debug("Skipped splitting document... already split!")
        else:
            #make sure there is an abstract or else create one
            
            if ( (len(self.indoc.getElementsByTagName("abstract")) < 1 ) &
            (len(self.indoc.getElementsByTagName("ABSTRACT")) < 1) ):
                #add abstract to paper
                self.addDummyAbstract()

            #do the annotating
            self.splitElement(self.indoc)

        with codecs.open(outfile,'w', encoding='utf-8') as f:
            self.indoc.writexml(f)

    def addDummyAbstract(self):
        """If no abstract is found, insert one"""

        dummytext = "No abstract available for this paper"

        logging.info("Adding dummy abstract...")

        if(len(self.indoc.getElementsByTagName("TITLE")) > 0):
            title = self.indoc.getElementsByTagName("TITLE")[0]
            nextEl = title.nextSibling
            paperEl = title.parentNode
            #create abstract
            el = self.indoc.createElement("ABSTRACT")
            text = self.indoc.createTextNode(dummytext)
            el.appendChild(text)
            paperEl.insertBefore(el, nextEl)

        if(len(self.indoc.getElementsByTagName("front")) > 0):
            #get the element
            front = self.indoc.getElementsByTagName("front")[0]
            nextEl = self.indoc.getElementsByTagName("permissions")[0].nextSibling
            abstractEl = self.indoc.createElement("abstract")
            parentEl = nextEl.parentNode
            titleEl = self.indoc.createElement("title")
            absec = self.indoc.createElement("sec")
            abp = self.indoc.createElement("p")

            abstractEl.appendChild(absec)
            absec.appendChild(titleEl)
            absec.appendChild(abp)
            abp.appendChild(self.indoc.createTextNode(dummytext))

            parentEl.insertBefore(abstractEl,nextEl)
    
    def splitElement(self, element):
        '''Split text found within element into sentences
        '''

        for node in element.childNodes:
            
            if node.nodeType == self.indoc.ELEMENT_NODE:

                if node.localName not in blacklist:
                    self.splitElement( node )

            elif node.nodeType == self.indoc.TEXT_NODE:

                logging.debug("Splitting text node %s" % node)
                
                text = node.wholeText

                if( len(text.strip()) < 1):
                    continue

                element.removeChild(node)

                for s in self.tokenizer.tokenize(text):
                    el = self.indoc.createElement("s")

                    tnode = self.indoc.createTextNode(s)
                    el.setAttribute("sid", str(self.nextSID))

                    el.appendChild(tnode)
                    element.appendChild(el)
                    self.nextSID += 1


