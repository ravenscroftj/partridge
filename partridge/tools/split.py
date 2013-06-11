'''
Module for splitting sentences on articles that need splitting
'''
import codecs
import logging
import cPickle
import os
import sys
import locale

from nltk.tokenize.punkt import PunktSentenceTokenizer

from xml.dom import minidom
from sets import Set

from text_sentence import Tokenizer

from partridge.config import config

sys.stdout = codecs.getwriter('utf8')(sys.stdout)

blacklist = set(['journal-id', 'journal-meta','article-id','article-categories'
'contrib','contrib-group', 'aff','pub-date','volume','issue','elocation-id',
'history','author-notes', 'copyright-statement', 'funding-group',
'copyright-year','counts','s', 'subj-group','author-notes', 'alt-title',
'title','ref-list','ack','meta','permissions', 'custom-meta-group',
'responseDate','request','header', 'xref', 'object-id'])

class SentenceSplitter:
    '''XML Aware sentence splitter for Partridge
    '''

    def __init__(self):
        self.nextSID = 1
        self.tokenizer = Tokenizer()
        self.inSentence = False

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
            
            #allocate the sentence IDs
            self.allocateSIDs()

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


    def allocateSIDs(self):
        """Go through the document and allocate SIDs for each sentence"""

        for node in self.indoc.getElementsByTagName("s"):
            node.setAttribute("sid", str(self.nextSID))
            self.nextSID += 1

    
    def splitElement(self, element):
        '''Split text found within element into sentences
        '''

        if (element.nodeType == self.indoc.ELEMENT_NODE) & (element.localName in blacklist):
            return

        text = ""
        boundary_nodes = []

        for node in element.childNodes:

            if node.nodeType == self.indoc.ELEMENT_NODE:
                boundary_nodes.append(node)

            if node.nodeType == self.indoc.TEXT_NODE:

                if text == "":
                    text = node.wholeText.strip()
                else:
                    text += " @@split_boundary@@ " + node.wholeText

        if len(text) > 0:

            for n in list(element.childNodes):
                print element.removeChild(n)
                

            sentence = ""
            el = self.indoc.createElement("s")
            
            for tok in list(self.tokenizer.tokenize(text)):

                if el == None:
                    el = self.indoc.createElement("s")

                
                if tok.value == "@@split_boundary@@":

                    print "Appended %s to %s" %(sentence,el.localName)
                    el.appendChild(self.indoc.createTextNode(sentence))
                    el.appendChild(boundary_nodes.pop(0))
                    sentence = ""


                elif tok.is_sent_start:
                    self.inSentence = True

                    if tok.is_upper:
                        sentence = tok.value.upper()
                    else:
                        sentence = tok.value.capitalize()

                elif (tok.value == ".") | (tok.value == ","):
                    sentence += tok.value
                else:
                    if tok.is_upper:
                        tok.value = tok.value.upper()

                    sentence += " " + tok.value

                if tok.is_sent_end:
                    self.inSentence = False
                    el.appendChild(self.indoc.createTextNode(sentence))
                    element.appendChild(el)

                    print "Appended %s to %s" %(sentence,el.localName)
                    el = None
                    sentence = ""

        
        for node in element.childNodes:
            if node.nodeType == self.indoc.ELEMENT_NODE:

                if(node.localName not in blacklist) & (not self.inSentence):
                    self.splitElement( node )

