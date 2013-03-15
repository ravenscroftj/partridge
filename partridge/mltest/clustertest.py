import Orange
import os
import logging
import sys

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

from partridge.config import config
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy

from partridge.models import db
from partridge.models.doc import Paper, PaperFile, Sentence, C_ABRV

from collections import Counter

from multiprocessing import Queue, Pool

from matplotlib import pyplot as plt 

from itertools import combinations

from extract_papers import get_best_k,build_table

#----------------------------------------------------------------------------

app = Flask(__name__)
app.config.update(config)

db.app = app
db.init_app(app)

papers = Paper.query.all()

corescs = C_ABRV.keys()

best_k = 0
best_score = 0.0
best_features = None

pone_ids = []
art_ids = []


for features in combinations(corescs, 3):
   

    print "Testing with features %s" % str(features)
    paper_table = build_table(papers, features)

    k,score = get_best_k(paper_table)

    km = Orange.clustering.kmeans.Clustering(paper_table, 3, maxiters=10,
                minscorechange=0)

    if score > best_score:
        print "%s are now best features with silhouette of %f for K=%d" % (
            str(features), score, k )

        best_features = features
        best_score = score
        best_k = k

    filename = "graphs/%s_%s_%s.png" % features

    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')

    colours = ['r','g','b']
    j = 0

    clusters = km.clusters

    for i in range(0, len(paper_table)):

        ax.scatter(paper_table[i][0],paper_table[i][1],paper_table[i][2],
        c=colours[clusters[i]])

        j += 1

    ax.set_xlabel(features[0])
    ax.set_ylabel(features[1])
    ax.set_zlabel(features[2])
    fig.savefig(filename)
    plt.close()






print "-----------------------------------------------------------"

print "Best combination is Features %s with K=%d (Silhouete %f)" % (
    str(best_features), best_k, best_score)
