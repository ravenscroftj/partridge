"""Train a Naive Bayes Filter using the results from the feature extraction"""

from __future__ import division

import nltk
import os
import cPickle


from nltk.probability import ELEProbDist, FreqDist

from nltk import NaiveBayesClassifier

from collections import defaultdict


from partridge.tools.paperstore import PaperParser
from partridge.util.manager import resultdir
from partridge.util.subjects import labels, collect_test_samples


samplecount = 0

def get_label_probdist(labelled_features):
    label_fd = FreqDist()
    for item,counts in labelled_features.items():
        for label in labels.values():
            if counts[label] > 0:
                label_fd.inc(label)

    label_probdist = ELEProbDist(label_fd)
    return label_probdist


def get_feature_probdist(labelled_features):
    feature_freqdist = defaultdict(FreqDist)
    feature_values = defaultdict(set)
    num_samples = samplecount
    for token, counts in labelled_features.items():
        for label in labels.values():
            feature_freqdist[label, token].inc(True, count=counts[label])
            feature_freqdist[label, token].inc(None, num_samples - counts[label])
            feature_values[token].add(None)
            feature_values[token].add(True)

    feature_probdist = {}
    for ((label, fname), freqdist) in feature_freqdist.items():
        probdist = ELEProbDist(freqdist, bins=len(feature_values[fname]))
        feature_probdist[label,fname] = probdist
    return feature_probdist



if __name__ == "__main__":


    label_count = {labels[x]:0 for x in labels }

    labelled_features = {}

    #collect test data for analysis of the classifier
    test_samples = collect_test_samples()

    print "Found %d test samples" % len(test_samples)
    
    for root, dirs, files in os.walk(resultdir):
    
        for file in files:
            print "Loading file %s " % file


            #increment sample count
            samplecount += 1

            with open(os.path.join(root,file),'rb') as f:
                fname, label, features = cPickle.load(f)

            for word in features:
                
                if word not in labelled_features:
                    labelled_features[word.lower()] = label_count
                
                labelled_features[word.lower()][label] += features[word]

            print "Currently at %d distinct tokens and %d papers" % (
                len(labelled_features), samplecount)

    label_probdist = get_label_probdist(labelled_features)

    feature_probdist = get_feature_probdist(labelled_features)

    classifier = NaiveBayesClassifier(label_probdist, feature_probdist)

    for samplefile in test_samples:
        features = {}

        p = PaperParser()
        p.parsePaper(samplefile)

        for sentence in p.extractRawSentences():
            tokens = nltk.word_tokenize(sentence)

            for word in tokens:
                features[word] = True

        dirname = os.path.basename(os.path.dirname(samplefile))
        label = labels[dirname]

        print "file: %s | actual: %s | predicted: %s" % (samplefile, label,
        classifier.classify(features))

    classifier.show_most_informative_features()
