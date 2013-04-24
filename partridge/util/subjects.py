import nltk
import os
import logging
import cPickle
import zlib

from multiprocessing import Pool

from partridge.models import db
from partridge.models.doc import Paper, PaperFile, Sentence, C_ABRV
from partridge.config import config

from partridge.tools.paperstore import PaperParser
from partridge.tools.split import SentenceSplitter

from flask import Flask

try:
    from collections import Counter
except:
    from partridge.util.counter import Counter

app = Flask(__name__)
app.config.update(config)

db.app = app
db.init_app(app)

corescs = C_ABRV.keys()

paper_root = "/home/james/dissertation/papers"
resultdir = "/home/james/dissertation/results"

labels = {
"plos_maths" : "Mathematics", 
"plos_compsci" : "Information Technology",
"plos_physics" : "Physics",
"plos_biochem" :" Biochemistry"
"plos_dna" : "DNA",
"plos_zoology" : "Zoology",
"plos_genetics" : "Genetics",
"plos_sociology" : "Sociology",
}


def parse_paper( (filename, label, data) ):
    
    print "Parsing %s" % filename

    p = PaperParser()
    p.parseString(data)

    sentences = []

    #return pos tagged sentences
    for sentence in p.extractRawSentences():
        tokens = nltk.word_tokenize(sentence)
        tagged = nltk.pos_tag(tokens)

        sentences.append(tagged)

    print "Found %d sentences in %s" %(len(sentences), filename)

    return (filename,sentences)


    #features = extract_features(p)
    #return (filename, label, features)


def collect_test_samples():

    results = []
    
    for root, dirs, files in os.walk(paper_root):
        
        for file in files:

            if file.endswith("_split.xml"):
                #see if there is a results file for this file
                if not os.path.exists( os.path.join(resultdir, file)):
                    results.append( os.path.join(root,file) )

    return results



def extract_features( paper_parser ):
    """Use the paper parser object to extract features"""
    wordfreq = {}
    
    print "Extracting sentences from paper..." 

    for sentence in paper_parser.extractRawSentences():
        tokens = nltk.word_tokenize(sentence)
        tagged = nltk.pos_tag(tokens)

        for word,tag in tagged:
            
            if (tag in interesting_tags) & (len(word) > 1):
                
                if word not in wordfreq:
                    wordfreq[word] = 1
                else:
                    wordfreq[word] += 1

    return wordfreq


def parse_paper_file( filename ):

    print "Parsing %s..." % filename

    dirname = os.path.basename(os.path.dirname(filename))
    label = labels[dirname]

    p = PaperParser()
    p.parsePaper(filename)

    features = extract_features(p)

    return (filename, label, features)
    
                


def process_file( file ):
    """Process a paper file in the queue"""

    if file.endswith("_split.xml"):
        print "Found a paper %s" % file
        parse_paper_file( file )

    elif file.endswith(".xml"):
        print "Found an unsplit paper"

        fname,ext = os.path.splitext(file)

        splitfile = fname + "_split" + ext

        if os.path.exists(splitfile):
            print "Split file exists for this paper"
        else:
            s = SentenceSplitter()
            s.split(file, splitfile)

            parse_paper_file( splitfile)


if __name__ == "__main__":

    papers = []

    p = Pool()

    for root,dirs,files in os.walk(paper_root):
        p.map( process_file, [os.path.join(root,file) for file in files])

logging.basicConfig(level=logging.INFO)

