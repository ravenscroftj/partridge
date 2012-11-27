'''
Module for splitting sentences on articles that need splitting
'''
import codecs
import logging

from nltk.tokenize.punkt import PunktSentenceTokenizer

from xml.dom import minidom
from sets import Set

blacklist = Set(['journal-id', 'journal-meta','article-id','article-categories'
'contrib','xref','aff','pub-date','volume','issue','elocation-id','history',
'copyright-statement', 'copyright-year','counts','s','subj-group','author-notes'
'title','ref-list','ack'])

logging.basicConfig(level=logging.DEBUG)

class SentenceSplitter:
    '''XML Aware sentence splitter for Partridge
    '''

    def __init__(self):
        self.tokenizer = PunktSentenceTokenizer()
        self.nextSID = 1

    def split(self, filename, outfile):
        
        #read the document
        with open(filename, 'rb') as f:
            self.indoc = minidom.parse(f)

        logging.debug("Parsed input file %s " % filename)

        self.splitElement(self.indoc)

        with codecs.open(outfile,'w', encoding='utf-8') as f:
            self.indoc.writexml(f)


    
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

                    artEl = self.indoc.createElement("annotationART")
                    artEl.setAttribute("type", "")

                    tnode = self.indoc.createTextNode(s)
                    el.setAttribute("sid", str(self.nextSID))

                    artEl.appendChild(tnode)
                    el.appendChild(artEl)
                    element.appendChild(el)
                    self.nextSID += 1


