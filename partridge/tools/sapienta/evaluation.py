from __future__ import division
from candc import SoapClient
from crf import Tagger, AttributeGenerator, Trainer
from docparser import SciXML
import cPickle
import crfsuite
import logging
import os
import pdb
import csv
'''
Created on 18 Apr 2012

@author: grabmuel
'''

logging.basicConfig()
logger = logging.getLogger('evaluation')
logger.setLevel(logging.INFO)

class Evaluation:
    
    def __init__(self):
        self.tagger = Tagger('/nfs/research2/textmining/grabmuel/aho/coresc/crfsuite/a.model')
        self.dirs = [ '/nfs/research2/textmining/grabmuel/coresc_corpus/combined' ]        

    def evaluateFile(self, path):
        logger.info('generating features for %s', path)
        parser = SciXML()
        doc = parser.parse(path)
        trueLabels = list(doc.getCorescLabels())
        #pdb.set_trace()
        
        predictedLabels, probabilities = self.tagger.getSentenceLabelsWithProbabilities(doc)
        self.calcPrecRecall(trueLabels, predictedLabels, probabilities)
        
    def pickleSentences(self):
        candcClient = SoapClient()
        
        for directory in self.dirs:
            outputPath = os.path.join(directory, 'pickled_M')
            files = [f for f in os.listdir(directory) if f.endswith('.xml') and not f.startswith('.')]
            #files = ['b412883d_mode2.Kamran.xml']
            for f in files:
                logger.info("pickling %s", f)
                parser = SciXML() # this is where I want to put PMC parser if I use that instead
                doc = parser.parse(os.path.join(directory, f))
                
                processedSentences = []
                for sentence in doc.yieldSentences():
                    candcFeatures = candcClient.getFeatures(sentence.content)
                    sentence.candcFeatures = candcFeatures
                    processedSentences.append(sentence)
                with open(os.path.join(outputPath, f), 'wb') as pickleFile:
                    cPickle.dump(processedSentences, pickleFile, -1)
                    
    def partitionFiles(self, numBlocks):
        folds = [[] for i in range(numBlocks)] 
        for directory in self.dirs:
            directory = os.path.join(directory, 'pickled')
            files = os.listdir(directory)
            for i, f in enumerate(files):
                path = os.path.join(directory, f)
                folds[i % numBlocks].append(path)
        return folds

    def partitionFilesFromCsv(self):
        with open('/nfs/research2/textmining/sapienta/Project/Development/Sapient2/corpora/output/All/FoldList/foldTable.csv', 'rb') as f:
            transposed = zip(*csv.reader(f))
            for foldColNumber in range(1, 9 * 3, 3): 
                foldCol = transposed[foldColNumber]
                annotatorCol = transposed[foldColNumber + 2]
                fileNames = zip(foldCol[2:], annotatorCol[2:])
                fileNames = [fileName for fileName in fileNames if not fileName[0] == '0']
                fileNames = ['_mode2.'.join(fileName) + '.xml' for fileName in fileNames]
                pickleDir = os.path.join(self.dirs[0], 'pickled')
                fileNames = [os.path.join(pickleDir, fileName) for fileName in fileNames]
                yield fileNames
    
    def trainFromPickles(self, trainingSet, modelPath):
        trainer = Trainer.PrintingTrainer()
        
        logger.info('using subset of size %d for training', len(trainingSet))
        for picklePath in trainingSet:
            labelSequence = crfsuite.StringList()
            itemSequence = crfsuite.ItemSequence() 
            with open(picklePath, 'rb') as f:
                logger.info('unpickling sentences from %s', picklePath)
                sentences = cPickle.load(f)
                
            for sentence in sentences:
                logger.debug('sentence: %s', sentence.content.encode('ascii', 'ignore'))
                label = str(sentence.corescLabel)
                labelSequence.append(label)
                
                item = crfsuite.Item()
                candcFeatures = sentence.candcFeatures
                candcFeatures.trigrams = [] # remove trigrams
                del sentence.candcFeatures
                for candcAttrib in AttributeGenerator.yieldCandcAttributes(candcFeatures):
                    logger.debug('parser feature: %s', candcAttrib.attr)
                    item.append(candcAttrib)
                for positionAttrib in AttributeGenerator.yieldPositionAttributes(sentence):
                    logger.debug('position feature: %s', positionAttrib.attr)
                    item.append(positionAttrib)
                itemSequence.append(item)
            trainer.append(itemSequence, labelSequence, 0)
                
        logger.info('finished unpickling and generating features, training...')
        trainer.select('l2sgd', 'crf1d')
        trainer.set('c2', '0.1')
        trainer.train(modelPath, -1)
        
    def evaluateFromPickles(self, testSet, modelPath):
        tagger = crfsuite.Tagger()
        tagger.open(modelPath)
        
        allTrueLabels = []
        allPredictedLabels = []
        allProbabilities = []
        
        logger.info('using subset of size %d for testing', len(testSet))
        for picklePath in testSet:
            itemSequence = crfsuite.ItemSequence()
            trueLabels = []
            
            with open(picklePath, 'rb') as f:
                logger.info('unpickling sentences from %s', picklePath)
                sentences = cPickle.load(f)
            
            for sentence in sentences:
                logger.debug('sentence: %s', sentence.content.encode('ascii', 'ignore'))
                label = str(sentence.corescLabel)
                trueLabels.append(label)
                
                item = crfsuite.Item()
                candcFeatures = sentence.candcFeatures
                candcFeatures.trigrams = [] # remove trigrams
                del sentence.candcFeatures
                for candcAttrib in AttributeGenerator.yieldCandcAttributes(candcFeatures):
                    logger.debug('parser feature: %s', candcAttrib.attr)
                    item.append(candcAttrib)
                for positionAttrib in AttributeGenerator.yieldPositionAttributes(sentence):
                    logger.debug('position feature: %s', positionAttrib.attr)
                    item.append(positionAttrib)
                itemSequence.append(item)
                
            tagger.set(itemSequence)
            predictedLabels = tagger.viterbi()
            probabilities = []
            for i, label in enumerate(predictedLabels):
                probability = tagger.marginal(label, i)
                probabilities.append(probability)
                #print '%s:%f' % (label, probability)

            #done with this file, add results to global list                
            allTrueLabels += trueLabels
            allPredictedLabels += predictedLabels
            allProbabilities += probabilities
            
        self.calcPrecRecall(allTrueLabels, allPredictedLabels, allProbabilities)
        
    @staticmethod
    def calcPrecRecall(trueLabels, predictedLabels, probabilities):
        labels = set(trueLabels).union(set(predictedLabels))
        tp = {}
        fp = {}
        fn = {}
        for label in labels:
            tp[label] = fp[label] = fn[label] = 0
        
        predictedZip = zip(predictedLabels, probabilities)
        print 'true label, predicted label, probability'
        for true, predictedZip in zip(trueLabels, predictedZip):
            predictedLabel, probability = predictedZip
            print true, predictedLabel, probability
            if true == predictedLabel:
                tp[true] += 1
            else:
                fp[predictedLabel] += 1
                fn[true] += 1
        for label in labels:
            print label
            if tp[label] == 0:
                prec = 0
                rec = 0
            else:
                prec = tp[label] / (tp[label] + fp[label])
                rec = tp[label] / (tp[label] + fn[label])
            print 'prec: %d tp / (%d tp + %d fp) = %f' % (tp[label], tp[label], fp[label], prec)
            print 'rec: %d tp / (%d tp + %d fn) = %f' % (tp[label], tp[label], fn[label], rec)
        # TODO macro prec/recall

if __name__ == '__main__':
    ev = Evaluation()
    #ev.pickleSentences()
    
    folds = list(ev.partitionFilesFromCsv())
    testSet = folds[0]
    trainingSet = folds[1:9]
    trainingSet = [f for fold in trainingSet for f in fold] #flatten
        
    modelPath = '/nfs/research2/textmining/sapienta/python_results/model_no0.model' 
    #ev.trainFromPickles(trainingSet, modelPath)
    ev.evaluateFromPickles(testSet, modelPath)

