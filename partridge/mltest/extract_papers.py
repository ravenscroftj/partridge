import Orange
import os

from partridge.config import config
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy

from partridge.models import db
from partridge.models.doc import Paper, PaperFile, Sentence, C_ABRV

from collections import Counter

from matplotlib import pyplot as plt 

#----------------------------------------------------------------------------

def plot_scatter(table, km, attx, atty, filename="kmeans-scatter", title=None):
    #plot a data scatter plot with the position of centeroids
    plt.rcParams.update({'font.size': 8, 'figure.figsize': [4,3]})
    x = [float(d[attx]) for d in table]
    y = [float(d[atty]) for d in table]
    colors = ["c", "w", "b"]
    cs = "".join([colors[c] for c in km.clusters])
    plt.scatter(x, y, c=cs, s=10)
    
    xc = [float(d[attx]) for d in km.centroids]
    yc = [float(d[atty]) for d in km.centroids]
    plt.scatter(xc, yc, marker="x", c="k", s=200)
    
    plt.xlabel(attx)
    plt.ylabel(atty)
    if title:
        plt.title(title)
    plt.savefig("%s-%s_vs%s.png" % (filename, attx, atty))
    plt.close()

#----------------------------------------------------------------------------

def plot_all_features(corescs, paper_table, km):
    done = []

    for i in corescs:
        for j in corescs:

            if( i == j ) or ( (j,i) in done): continue

            plot_scatter(paper_table, km, i, j)

            done.append( (i,j) )

#----------------------------------------------------------------------------

def find_paper_ids( dir ):

    ids = []

    for root, dirs, files in os.walk(dir):
        
        for file in files:
            name,ext = os.path.splitext(file)

            if ext == ".xml":
                pfile = PaperFile.query.filter(
                    PaperFile.path.like("%%%s%%" % name)).first()

                if(pfile != None):
                    ids.append(pfile.paper_id)

    return ids

#----------------------------------------------------------------------------

def get_best_k(paper_table):

    bestk = 0
    bestscore = 0.0

    for k in range(2,8):

        km = Orange.clustering.kmeans.Clustering(paper_table, k, maxiters=10,
                minscorechange=0)

        score = Orange.clustering.kmeans.score_silhouette(km)

        print k,score

        if score > bestscore:
            bestk = k
            bestscore = score

    print "Selected best k value %s for silhouette visualisation" % bestk
    return bestk,bestscore

#----------------------------------------------------------------------------



#set up data domain
class_var = Orange.feature.Discrete("type")
class_var.add_value("Research")
class_var.add_value("Review")
class_var.add_value("Case Study")


def build_table( papers, features):


    #set up orange domain
    domain = Orange.data.Domain([Orange.feature.Continuous(x) for x in
    features], class_var)

    paper_table = Orange.data.Table(domain)
    for key in ['source','title']:
        newid = Orange.feature.Descriptor.new_meta_id()
        domain.add_meta(newid, Orange.feature.String(key))

    for paper in papers:

        if len(paper.sentences) < 1:
            continue

        if(paper.type == None):
            continue


        inst_list = []
        sentdist = paper.sentenceDistribution(True)
        for f in features:
            inst_list.append( sentdist[f] * 100 / len(paper.sentences) )

        inst_list.append(str(paper.type))
            
        inst = Orange.data.Instance(domain, inst_list)

        inst['title'] = str(paper.title.encode('ascii', 'ignore'))

        #if( paper.id in pone_ids):
        #    inst['source'] = "pone"
        #elif( paper.id in art_ids):
        #    inst['source'] = "art"

        paper_table.append(inst)


    return paper_table


#----------------------------------------------------------------------------

if __name__ == "__main__":
    app = Flask(__name__)
    app.config.update(config)

    db.app = app
    db.init_app(app)

    #find paper sources
    PLOSONE_DIR = "/home/james/dissertation/papers/plos"
    ART_DIR = "/home/james/dissertation/papers/art"

    pone_ids = set ( find_paper_ids( PLOSONE_DIR ) )
    art_ids  = set ( find_paper_ids( ART_DIR ))

    papers = Paper.query.all()

    corescs = ['Bac', 'Model', 'Obj'] #C_ABRV.keys()

    print "Building data table"
    paper_table = build_table(papers, corescs)

    print "Clustering Data..."


    k = 2

    km = Orange.clustering.kmeans.Clustering(paper_table, k, maxiters=10, minscorechange=0)
    Orange.clustering.kmeans.plot_silhouette(km, "kmeans-silhouette.png")

    clusters = []

    for i in range(0,k):
        clusters.append([])    

    for i in range(0, len(km.clusters)):

        clusters[ km.clusters[i] ].append( paper_table[i])


    c = Counter() 
        

    for cluster in clusters:
        print "---------------------------------------"
        sources = [ str(paper['source']) for paper in cluster]
        c = Counter(sources)
        print c
        print "---------------------------------------"

    #for paper in clusters[0]:
    #
    #    if str(paper['source']) == 'art':
    #        print paper['title']
