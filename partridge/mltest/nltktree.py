from __future__ import division

import os
import sys
import random
from math import ceil

from partridge.config import config
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy

from matplotlib import pyplot as plt

from partridge.models import db
from partridge.models.doc import Paper, PaperFile, Sentence, C_ABRV

from partridge.mltest.paper_tree import find_paper_ids, TYPE_DIRS, FEATURES

from nltk.classify.util import apply_features, accuracy
from nltk.classify.decisiontree import DecisionTreeClassifier

from progressbar import ProgressBar


app = Flask(__name__)
app.config.update(config)

db.app = app
db.init_app(app)

types = {}
for paper_type in TYPE_DIRS:
    types[paper_type] = set(find_paper_ids(TYPE_DIRS[paper_type]))
    
    print "Found %d %s papers" % (len(types[paper_type]), paper_type)
    

all_ids = set()

for type in types:
    all_ids |= types[type]

print "Found %d papers in total" % len(all_ids)

total_papers = len(all_ids)


def paper_features( pid, pbar):
    
    paper = Paper.query.filter(Paper.id==pid).first()

    sentdist = paper.sentenceDistribution(True)

    features = {}

    for coresc in FEATURES:
        features[coresc] = sentdist[coresc] * 100 / len(paper.sentences)

    paper_features.i += 1
    print "Features retrieved for paper %d (#%d)" % (paper.id,paper_features.i)
    #pbar.update(paper_features.i)

    return features

paper_features.i = 0

all_data = [ (id,type) for type in types for id in types[type] ]

d = int(0.8 * len(all_data) )

random.shuffle(all_data)


training = all_data[:d]
testing  = all_data[d:]


pbar = ProgressBar(maxval=total_papers).start()
tree = DecisionTreeClassifier.train(
apply_features(lambda x: paper_features(x, pbar) ,training))
pbar.finish()

print accuracy(tree, testing)
