from __future__ import division
'''
Created on 12 Mar 2012

@author: grabmuel
'''

import xml.parsers.expat
import unittest
import math

class Document:
    def __init__(self):
        self.headers = []
        self.numSentencesTotal = 0
        self.hightesWordCount = 0
        
    def setHighestWordCount(self, sentence):
        numWords = len(sentence.content.split(' '))
        if numWords > self.hightesWordCount:
            self.hightesWordCount = numWords
        
    def addHeader(self, header):
        self.headers.append(header)
        
    def getAbsoluteSentenceLocation(self, sentCountDoc):
        '''
        Calculate the 'Absolute Location' feature of a sentence.
        
        TODO: READ TEUFEL 2000
        '''
        norm = sentCountDoc / (self.numSentencesTotal + 0.1)
        charNum = int(math.floor(norm * 10)) + 65
        letter = chr(charNum)
        return letter
    
    def getHeaderId(self, headerIndex):
        '''
        Calculate the 'SectionId' feature of a section.
        Simply return the header/section number, starting from 1, maximum value is 10.
        '''
        paragraphNumber = headerIndex + 1
        if paragraphNumber > 10:
            return 10
        else:
            return paragraphNumber
        
    def getSentenceLength(self, sentence):
        '''
        Caclualte the 'Length' feature of a sentence.
        TODO: get proper specification
        For now split into 10 equal partitions (A-J), scaled to using the longest 
        sentence in the document.
        '''
        numWords = len(sentence.content.split(' ')) #move to function
        norm = numWords / (self.hightesWordCount + 0.1)
        charNum = int(math.floor(norm * 10)) + 65
        letter = chr(charNum)
        return letter
    
    def getCorescLabels(self):
        for header in self.headers:
            for para in header.paragraphs:
                for sent in para.sentences:
                    yield sent.corescLabel
            
    def yieldSentences(self):
        for header in self.headers:
            for para in header.paragraphs:
                for sentence in para.sentences:
                    self.numSentencesTotal += 1
                    self.setHighestWordCount(sentence)
                    header.numSentencesInHeader += 1
                    
        sentCountDoc = 0
        for headerIndex, header in enumerate(self.headers):
            sentCountHeader = 0
            headerId = self.getHeaderId(headerIndex)
            headerType = header.getHeaderType()
            for para in header.paragraphs:
                sentCountPara = 0
                for sentence in para.sentences:
                    sentCountDoc += 1
                    sentCountHeader += 1
                    sentCountPara += 1
                    
                    sentence.absoluteLocation = self.getAbsoluteSentenceLocation(sentCountDoc)
                    sentence.headerId = headerId
                    sentence.locationInHeader = header.getSentenceLocationInHeader(sentCountHeader)
                    sentence.locationInPara = para.getSentenceLocationInPara(sentCountPara)
                    sentence.headerType = headerType
                    sentence.locationInHeader2 = header.getSentenceLocationInHeader2(sentCountHeader)
                    sentence.length = self.getSentenceLength(sentence)
                    yield sentence
                    
    def addPredictedLabels(self, predictedLabels):
        i = 0
        for header in self.headers:
            for para in header.paragraphs:
                for sentence in para.sentences:
                    sentence.corescLabel = predictedLabels[i]
                    i += 1
                    
class Header:
    def __init__(self):
        self.name = ''
        self.paragraphs = []
        self.numSentencesInHeader = 0
        
    def addParagraph(self, para):
        self.paragraphs.append(para)
        
    def getSentenceLocationInHeader(self, sentCountHeader):
        '''
        Calcualte the 'Struct-1' feature for a sentence.
        Sentence location within a section split into 3 equal partitions (C, D, E).
        Move sentence     1 to class A
                          2 & 3 to class B
                          -2 & -3 to class F
                          -1 to class G  
        '''
        numSentences = self.numSentencesInHeader
        if sentCountHeader == 1:
            return 'A'
        elif sentCountHeader == 2 or sentCountHeader == 3:
            return 'B'
        elif sentCountHeader == (numSentences - 1) or sentCountHeader == (numSentences - 2):
            return 'F'
        elif sentCountHeader == (numSentences):
            return 'G'
        else:
            norm = sentCountHeader / (self.numSentencesInHeader + 0.1)
            charNum = int(math.floor(norm * 10 / 3)) + 65
            letter = chr(charNum)
            return letter
        
    def getHeaderType(self):
        '''
        Calculate the 'Struct-3' feature of a header.
        Try to normalize to one of 14 heading type classes by finding substrings
        (or exact matches for that matter). Two special classes for empty and non-matching.
        '''
        substringToType = {
                   'abstract': 'abstract',
                   'appendix': 'appendix',
                   'acknowledgement': 'appendix',
                   'intro': 'introduction',
                   'background': 'background',
                   'previous': 'background',
                   'model': 'model',
                   'theor': 'theory',
                   'calculation': 'calculation',
                   'computational': 'computational',
                   'experiment': 'experiment',
                   'result': 'result',
                   'method': 'method',
                   'mechanism': 'mechanism',
                   'summar': 'summary',
                   'conclu': 'conclusion',
                   'discuss': 'discussion'
                   }
        if self.name == '':
            return 'none'
        for subString, htype in substringToType.items():
            if subString in self.name.lower():
                return htype
        return 'specific'
    
    def getSentenceLocationInHeader2(self, sentCountHeader):
        '''
        Calculate the 'location in section' feature.
        Sentence location withing a Header is split into 5 equal partitions (A-E).
        '''
        norm = sentCountHeader / (self.numSentencesInHeader + 0.1)
        charNum = int(math.floor(norm * 10 / 2)) + 65
        letter = chr(charNum)
        return letter        
            
class Paragraph:
    def __init__(self):
        self.sentences = []
        
    def addSentence(self, sentence):
        self.sentences.append(sentence)
        
        
    def getSentenceLocationInPara(self, sentCountPara):
        '''
        Cacluclate the 'Struct-2' feature for a sentence.
        Sentence location within a paragraph split into 5 equal partitions (A-E).
        '''
        norm = sentCountPara / (len(self.sentences) + 0.1)
        charNum = int(math.floor(norm * 10 / 2)) + 65
        letter = chr(charNum)
        return letter


class Sentence:
    def __init__(self, corescLabel=''):
        self.corescLabel = corescLabel
        self.content = ''
        self.numCitations = 0
        #computed after whole document is parsed
        self.absoluteLocation = ''
        self.headerId = 0
        self.locationInHeader = '' #aka 'Struct-1'
        self.locationInPara = '' #aka 'Struct-2'
        self.headerType = '' #aka 'Strict-3'
        self.locationInHeader2 = ''
        self.length = ''
        self.sid = 0 #initialise sentence ID (ravenscroftj)
        
    def addText(self, text):
        self.content += text
        
    def incrementCitations(self):
        if self.numCitations < 2:
            self.numCitations += 1
        
    def getNumWords(self):
        return len(self.content.split(' '))
        
    def __str__(self):
        return '%s|%s|cite %d|%s' % (self.corescLabel, self.absoluteLocation,
                                    self.numCitations, self.content)
    
    def __repr__(self):
        str(self)   

class SciXML:
    
    def __init__(self):
        self.doc = Document()
        self.inHeader = self.inParagraph = self.inAnnotation = False
        self.currHeader = self.currParagraph = self.currSentence = None
        
        #initialise sentence finding vars (ravenscroftj)
        self.inSentence = False
        self.currentSentenceID = None

        #initialise first header for metadata and such (ravenscroftj)
        #self.currHeader = Header()
        #self.doc.addHeader(self.currHeader)
        #self.currParagraph = Paragraph()
        #self.currHeader.addParagraph(self.currParagraph)

    def startElement(self, name, attrs):
        if name.upper() == 'ABSTRACT':
            header = Header()
            header.name = 'Abstract'
            self.doc.addHeader(header)
            self.currHeader = header
            
            para = Paragraph()
            self.currHeader.addParagraph(para)
            self.currParagraph = para
        elif name.upper() == 'HEADER':
            self.inHeader = True
            header = Header()
            self.doc.addHeader(header)
            self.currHeader = header
        #detect sentence elements and pick up sentence ID (ravenscroftj)
        elif name == 's':
            self.inSentence = True
            self.currentSentenceID = attrs['sid']
        #end change

        #detect sections and titles in scixml (ravenscroftj)
        elif name == "sec":
            self.inHeader = True
            header = Header()
            self.doc.addHeader(header)
            self.currHeader = header
        #end change

        elif name.upper() == 'P':
            self.inParagraph = True
            para = Paragraph()

            if(self.currHeader != None):
                self.currHeader.addParagraph(para)

            self.currParagraph = para
        elif name == 'annotationART':
            if self.currParagraph == None:
                return # skipping annotation in title
            self.inAnnotation = True
            label = attrs['type']
            sent = Sentence(label)
            #add sentence ID to sentence object (ravenscroftj)
            sent.sid = self.currentSentenceID
            self.currParagraph.addSentence(sent)
            self.currSentence = sent
        elif name.upper() == 'REF' and self.inAnnotation:
            self.currSentence.incrementCitations()
            
    def endElement(self, name):
        if name.upper() == 'HEADER':
            self.inHeader = False
        elif name.upper() == 'P':
            self.inParagraph = False

        #detect end of section in scixml (ravenscroftj)
        elif name == "sec" or name == "abstract":
            self.inHeader = False
        #end change

        elif name == 's':
            self.inSentence = False
        elif name == 'annotationART':
            self.inAnnotation = False
    
    def charData(self, data):
        if self.inHeader:
            self.currHeader.name += data
        elif self.inAnnotation:
            self.currSentence.addText(data)
    
    def parse(self, path):
        parser = xml.parsers.expat.ParserCreate()
        parser.StartElementHandler = self.startElement
        parser.EndElementHandler = self.endElement
        parser.CharacterDataHandler = self.charData
        parser.ParseFile(open(path))
        return self.doc

class TestSciXML(unittest.TestCase):
    testFile = '/home/james/tmp/b103844n_mode2.Andrew.xml'
    
    def testParse(self):
        parser = SciXML()
        doc = parser.parse(TestSciXML.testFile)
        sentences = list(doc.yieldSentences())
        self.assertEqual(28, len(doc.headers)) #27 'real' headers from body, plus abstract
        self.assertEqual(244, doc.numSentencesTotal) #245 minus title
        self.runFirstSentence(sentences)
        self.runMiddleSentence(sentences)
        self.runLastSentence(sentences)

    def runFirstSentence(self, sentences):
        firstSentence = sentences[0]
        self.assertEqual('Res', firstSentence.corescLabel)
        self.assertEqual(u'A series of transient interconvertible protonated and deprotonated mononuclear Fe(iii) peroxo species are derived from the pH dependent reaction of dihydrogen peroxide with mononuclear iron(ii) or iron(iii) complexes of general formulation [Fe(Rtpen)X](A)n, n = 1, 2; X = Cl, Br; Rtpen = N-alkyl-N,N\xe2\x80\xb2,N\xe2\x80\xb2-tris(2-pyridylmethyl)ethane-1,2-diamine, alkyl = R = CH3CH2, CH3CH2CH2, HOCH2CH2, (CH3)2CH, C6H5, and C6H5CH2; A = ClO4, PF6.', firstSentence.content)
        self.assertEqual('A', firstSentence.absoluteLocation) #incorrect implementation
        self.assertEqual(1, firstSentence.headerId)
        self.assertEqual('A', firstSentence.locationInHeader)
        self.assertEqual('A', firstSentence.locationInPara)
        self.assertEqual('abstract', firstSentence.headerType)
        self.assertEqual('A', firstSentence.locationInHeader2)
        self.assertEqual('H', firstSentence.length)
        self.assertEqual(0, firstSentence.numCitations)


    def runMiddleSentence(self, sentences):
        middleSentence = sentences[98]
        self.assertEqual('Exp', middleSentence.corescLabel)
        self.assertEqual(u'The structures were solved by direct methods, using SIR97, and structures were refined on F using the modification ORFLS in KRYSTAL, hydrogen atoms were constrained to chemically reasonable positions with Uiso = 1.2Ueq for the atoms to which they were attached, except for the hydroxyl hydrogen atom of [Fe(etOHtpen)Cl]PF6 which was located from a difference map and refined isotropically.', middleSentence.content)
        self.assertEqual('E', middleSentence.absoluteLocation)
        self.assertEqual(10, middleSentence.headerId)
        self.assertEqual('B', middleSentence.locationInHeader)
        self.assertEqual('C', middleSentence.locationInPara)
        self.assertEqual('specific', middleSentence.headerType)
        self.assertEqual('C', middleSentence.locationInHeader2)
        self.assertEqual('I', middleSentence.length)
        self.assertEqual(2, middleSentence.numCitations)


    def runLastSentence(self, sentences):
        lastSentence = sentences[-1]
        self.assertEqual('Con', lastSentence.corescLabel)
        self.assertEqual('The kinetic studies on the formation of a mononuclear non-heme iron peroxides support an Ia mechanism with 7-coordinate iron(iii) in the transition state.', lastSentence.content)
        self.assertEqual('J', lastSentence.absoluteLocation)
        self.assertEqual(10, lastSentence.headerId)
        self.assertEqual('G', lastSentence.locationInHeader)
        self.assertEqual('E', lastSentence.locationInPara)
        self.assertEqual('conclusion', lastSentence.headerType)
        self.assertEqual('E', lastSentence.locationInHeader2)
        self.assertEqual('D', lastSentence.length)
        self.assertEqual(0, lastSentence.numCitations)


if __name__ == '__main__':
    unittest.main()
    #s = SciXML()
    #doc = s.parse(TestSciXML.testFile)
    #for sent in doc.yieldSentences(): print sent

#export PYTHONPATH=/nfs/research2/textmining/grabmuel/aho/coresc/crfsuite/usr_local_lib/python2.7/dist-packages:/nfs/research2/textmining/grabmuel/aho/coresc/python-suds-0.4
#export LD_LIBRARY_PATH=/nfs/research2/textmining/grabmuel/aho/coresc/crfsuite/usr_local_lib
