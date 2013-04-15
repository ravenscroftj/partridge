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

from extract_papers import get_best_k,build_table, find_paper_ids

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
pubmed_ids = []

print "finding paper sources..."

art_dir = "/home/james/dissertation/papers/art"
papers_dir = "/home/james/dissertation/data/processed"

for root,dirs,files in os.walk(papers_dir):
    for file in files:
        name,ext = os.path.splitext(file)

        if ext == ".xml":
            pfile = PaperFile.query.filter(
                    PaperFile.path.like("%%%s%%" % name)).first()

            if(pfile != None):

                if name.startswith("journal.p"):
                    pone_ids.append(pfile.paper_id)
                elif name.startswith("pmc"):
                    pubmed_ids.append(pfile.paper_id)
                elif os.path.exists( os.path.join(art_dir, name.split("_")[0] +
                ".xml")):
                    art_ids.append(pfile.paper_id)

art_ids = set(art_ids)
pubmed_ids = set(pubmed_ids)
pone_ids = set(pone_ids)

print "Found %d art papers, %d PMC papers and %d PloSOne papers" % (
len(art_ids), len(pubmed_ids), len(pone_ids))

corescs = ["Bac","Met","Mot"]
for features in combinations(corescs, 3):
   

    print "Testing with features %s" % str(features)
    paper_table = build_table(papers, features, pone_ids, art_ids, pubmed_ids)

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

    colours = {"pone" : 'r', "art" : 'g', "pubmed" : 'b', "other" : 'y'}
    j = 0

    clusters = km.clusters

    for i in range(0, len(paper_table)):

        ax.scatter(paper_table[i][0],paper_table[i][1],paper_table[i][2],
        c=colours[str(paper_table[i]["source"])])

    ax.set_xlabel(features[0])
    ax.set_ylabel(features[1])
    ax.set_zlabel(features[2])
    fig.savefig(filename)
    plt.close()




print "-----------------------------------------------------------"

print "Best combination is Features %s with K=%d (Silhouete %f)" % (
    str(best_features), best_k, best_score)
