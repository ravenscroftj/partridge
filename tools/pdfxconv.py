#!/usr/bin/python2
'''
This script enables the conversion of a PDF document to XML recognised by Sapienta via pdfx

'''
import os
import pycurl
import StringIO
import codecs

from progressbar import ProgressBar
from optparse import OptionParser
from xml.dom import minidom

from nltk.tokenize import word_tokenize, sent_tokenize

PDFX_URL = "http://pdfx.cs.man.ac.uk"

class PDFXConverter:

    nextSID = 1

    #---------------------------------------------------------------------------------------------   

    def convert(self, filename, outfile):

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


       print "Writing result to %s" % outfile
       #write resulting xml file
       with codecs.open(outfile,'w', encoding='utf-8') as f:
            self.outdoc.writexml(f)
    #---------------------------------------------------------------------------------------------   

    def __processXML(self):
        '''Given some input XML, process it and make it sapienta friendly
        '''

        #set up input and output xml docs
        self.indoc = minidom.parseString(self.result)
        self.initxml() 

        #get front tag
        frontEl = self.indoc.getElementsByTagName("front")[0]


        #copy input title
        articleTitle = frontEl.getElementsByTagName("article-title")[0].firstChild.data

        self.sentence_split( articleTitle, self.titleEl)

        #self.titleEl.appendChild(self.outdoc.createTextNode( articleTitle))

        #copy abstract or produce warning
        abstractEls = frontEl.getElementsByTagName("abstract")
        
        if( len(abstractEls) < 1):
            print "No abstract found, missclassified? Checking for 'misc text data' in front section of document"

            abstract = ""
            
            for region in frontEl.getElementsByTagName("region"):

                if( region.getAttribute('class') == 'DoCO:TextChunk'):
                    #figure out how many words the region has
                    text = self.getText( region )
                    words = word_tokenize(text)
                    
                    if( len(words) > 50):
                        abstract = text
                        #delete this region so that it is not used in any further computation
                        frontEl.removeChild(region)
                        #break the for loop
                        break
        
        else:
            abstract = abstractEls[0].firstChild.data

        self.sentence_split(abstract, self.abstractEl)
        #self.abstractEl.appendChild(self.outdoc.createTextNode( abstract ) )


        #now process all other text nodes


        text = ""

        for region in self.indoc.getElementsByTagName("region"):
            
            if(region.hasAttribute("class") and region.getAttribute("class") == 'DoCO:TextChunk'):
                #self.bodyEl.appendChild( self.outdoc.createTextNode( self.getText(region) ) )
                text += self.getText(region) + " "
        
        self.sentence_split(text, self.bodyEl)
        
    def getText(self, el):
        '''Concat all text from child elements together'''

        result = ""

        for node in el.childNodes:

           if node.nodeType == node.TEXT_NODE:
               result += node.data

           else:
               result += self.getText(node)

        return result
    
    #---------------------------------------------------------------------------------------------   
    
    def sentence_split(self, text, parentNode):
        '''Use NLTK to run a sentence splitter over the document

        Takes text and splits into sentences then appends <s> 
        elements to the parentNode for each sentence
        '''
        
        for sent in sent_tokenize(text):

            #see how long the sentence is and if we can just ignore it
            if(len(sent) < 5):
                continue
            
            sEl = self.outdoc.createElement("s")
            sEl.appendChild(self.outdoc.createTextNode(sent))
            sEl.setAttribute("sid", str(self.nextSID))
            parentNode.appendChild(sEl)
            self.nextSID += 1
 

    #---------------------------------------------------------------------------------------------   

    def initxml(self):
        self.outdoc = minidom.Document()

        #set up basic scixml self.outdoc
        self.paperEl = self.outdoc.createElement("PAPER")
        self.outdoc.appendChild(self.paperEl)
        #set up title element
        self.titleEl = self.outdoc.createElement("TITLE")
        self.paperEl.appendChild(self.titleEl)
        #abstract element
        self.abstractEl = self.outdoc.createElement("ABSTRACT")
        self.paperEl.appendChild(self.abstractEl)
        #body element
        self.bodyEl = self.outdoc.createElement("BODY")
        self.paperEl.appendChild(self.bodyEl)

            
    #---------------------------------------------------------------------------------------------   
    
    def __progress(self, download_t, download_d, upload_t, upload_d):
        '''Curl callback method used to display progress to user
        '''
        self.progress.update(upload_d)

    #---------------------------------------------------------------------------------------------   

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
        p.convert(infile, outfile)
