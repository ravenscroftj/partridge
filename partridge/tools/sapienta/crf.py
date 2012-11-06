from __future__ import division
'''
Created on 7 Mar 2012

@author: grabmuel
'''

import crfsuite
import sys
from candc import SoapClient
import unicodedata
from docparser import SciXML
import os
import logging
import pdb

logging.basicConfig()
logger = logging.getLogger('crf')
logger.setLevel(logging.INFO)

class AttributeGenerator:
    
    @staticmethod
    def createUnicodeAttribute(uni):
        ascii = unicodedata.normalize('NFKD', uni).encode('ascii', 'ignore')
        return crfsuite.Attribute(ascii)
    
    @staticmethod
    def yieldCandcAttributes(candcFeatures):
        for label, ngrams in {'unigram':candcFeatures.unigrams, 'bigram':candcFeatures.bigrams, 'trigram':candcFeatures.trigrams}.items():
            for ngram in ngrams:
                if isinstance(ngram, tuple):
                    ngram = '|'.join(ngram)
                field = '%s=%s' % (label, ngram)
                yield AttributeGenerator.createUnicodeAttribute(field)
                
        for verb in candcFeatures.verbs:
            field = 'verb=' + verb
            yield AttributeGenerator.createUnicodeAttribute(field)
            
        for verbClass in candcFeatures.verbClasses:
            field = 'verbclass=' + verbClass
            yield AttributeGenerator.createUnicodeAttribute(field)
            
        for verbPos in candcFeatures.verbsPos:
            field = 'verbPos=' + verbPos
            yield AttributeGenerator.createUnicodeAttribute(field)
        
        if candcFeatures.passive:
            field = u'passive=yes' 
        else:
            field = u'passive=no'
        yield AttributeGenerator.createUnicodeAttribute(field)
            
        for triple in candcFeatures.relationTriples:
            field = 'triple=' + '|'.join(triple)
            yield AttributeGenerator.createUnicodeAttribute(field)
            
        for relation, targets in candcFeatures.relationMap.items():
            for target in targets:
                field = '%s=%s' % (unicode(relation), target)
                yield AttributeGenerator.createUnicodeAttribute(field)
                
    @staticmethod
    def yieldPositionAttributes(sentence):
        for variable, value in vars(sentence).items():
            if variable not in ('corescLabel', 'content'):
                field = u'%s=%s' % (variable, value)
                yield AttributeGenerator.createUnicodeAttribute(field)

class Trainer:
    class PrintingTrainer(crfsuite.Trainer):
        def message(self, s):
            sys.stdout.write(s)
            
    def trainModel(self, modelPath):
        labelSequence = crfsuite.StringList()
        itemSequence = crfsuite.ItemSequence()
        candcClient = SoapClient()

        dirs = [
                '/nfs/research2/textmining/grabmuel/coresc_corpus/TierA',
                #'/nfs/research2/textmining/grabmuel/coresc_corpus/TierB'
                ]
        for directory in dirs:
            files = [f for f in os.listdir(directory) if f.endswith('.xml') and not f.startswith('.')]
            for f in files:
                logger.info("adding features of %s" + f)
                parser = SciXML()
                doc = parser.parse(os.path.join(directory, f))
                
                for sentence in doc.yieldSentences():
                    logger.debug('sentence: %s', sentence.content.encode('ascii', 'ignore'))
                    label = str(sentence.corescLabel)
                    labelSequence.append(label)
                    
                    item = crfsuite.Item()
                    candcFeatures = candcClient.getFeatures(sentence.content)
                    for candcAttrib in AttributeGenerator.yieldCandcAttributes(candcFeatures):
                        logger.debug('parser feature: %s', candcAttrib.attr)
                        item.append(candcAttrib)
                    for positionAttrib in AttributeGenerator.yieldPositionAttributes(sentence):
                        logger.debug('position feature: %s', positionAttrib.attr)
                        item.append(positionAttrib)
                    itemSequence.append(item)
        logger.info('done generating features, training...')
            
        trainer = Trainer.PrintingTrainer()
        trainer.append(itemSequence, labelSequence, 0)
        trainer.select('l2sgd', 'crf1d')
        trainer.set('c2', '0.1')
        trainer.train(modelPath, -1)
    
class Tagger:
    def __init__(self, modelpath):
        self.tagger = crfsuite.Tagger()
        self.tagger.open(modelpath)
        logger.info('model loaded')
        self.candcClient = SoapClient()
        
    def getSentenceLabelsWithProbabilities(self, doc):
        itemSequence = crfsuite.ItemSequence()
        sids = []

        for sentence in doc.yieldSentences():
            sids.append(sentence.sid)
            logger.debug('sentence: %s', sentence.content.encode('ascii', 'ignore'))
            item = crfsuite.Item()
            candcFeatures = self.candcClient.getFeatures(sentence.content)
            for candcAttrib in AttributeGenerator.yieldCandcAttributes(candcFeatures):
                logger.debug('parser feature: %s', candcAttrib.attr)
                item.append(candcAttrib)
            for positionAttrib in AttributeGenerator.yieldPositionAttributes(sentence):
                logger.debug('position feature: %s', positionAttrib.attr)
                item.append(positionAttrib)
            itemSequence.append(item)
        logger.info('...done generating features, tagging')
        self.tagger.set(itemSequence)
        predictedLabels = zip(sids, self.tagger.viterbi())
        probabilities = []
        for i, label in enumerate(predictedLabels):
            probability = self.tagger.marginal(label[1], i)
            probabilities.append(probability)
            #print '%s:%f' % (label, probability)
        return predictedLabels, probabilities


def runTagger(indoc):
    tagger = Tagger('a.model')
    parser = SciXML()
    doc = parser.parse(indoc)
    labels, probabilites = tagger.getSentenceLabelsWithProbabilities(doc)
    print labels
            
if __name__ == '__main__':
    #Trainer().trainModel('/nfs/research2/textmining/grabmuel/aho/coresc/crfsuite/no.model')
    #runTagger()
    
    if( len(sys.argv) < 2):
        print "Provide a document to tag"
    else:
        indoc = sys.argv[1]
        runTagger(indoc)
    
    
#/nfs/research2/textmining/grabmuel/aho/coresc/crfsuite/crfsuite-0.12-x86_64/bin/crfsuite dump /nfs/research2/textmining/grabmuel/aho/coresc/crfsuite/a.model
#TierA: 36 min total, 16 minutes for training
#old model: /nfs/research2/textmining/sapienta/Project/Development/Sapient2/corpora/output/All/no_stop_Fold4/all_Models/Fold4_crfsuite_allmodel.model
