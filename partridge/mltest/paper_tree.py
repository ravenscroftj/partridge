import Orange,orngTree
import os

from partridge.config import config
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy

from partridge.models import db
from partridge.models.doc import Paper, PaperFile, Sentence, C_ABRV

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


app = Flask(__name__)
app.config.update(config)

db.app = app
db.init_app(app)

#find paper sources
REVIEW_DIR   = "/home/james/dissertation/papers/training/review"
RESEARCH_DIR = "/home/james/dissertation/papers/training/research"
CASE_DIR     = "/home/james/dissertation/papers/training/case"


research_ids = set( find_paper_ids( RESEARCH_DIR ) )
print "Found %d research papers" % len(research_ids)

review_ids   = set( find_paper_ids( REVIEW_DIR ) )
print "Found %d review papers" % len(review_ids)


case_ids   = set( find_paper_ids( CASE_DIR ) )
print "Found %d case study papers" % len(case_ids)

all_ids = review_ids.union(research_ids).union(case_ids)

papers = Paper.query.filter(Paper.id.in_(all_ids)).all()

#set up data domain
class_var = Orange.feature.Discrete("type")
class_var.add_value("Research")
class_var.add_value("Review")
class_var.add_value("Case Study")

FEATURES = C_ABRV.keys()

domain = Orange.data.Domain([Orange.feature.Continuous(x) for x in FEATURES], 
class_var)


paper_table = Orange.data.Table(domain)
print "Loading Data..."

for paper in papers:
    

    if len(paper.sentences) < 1:
        continue

    inst_list = []
    sentdist = paper.sentenceDistribution(True)
    for coresc in FEATURES:
        inst_list.append( sentdist[coresc] * 100 / len(paper.sentences) )
        
    if(paper.id in review_ids):
        inst_list.append("Review")
    elif( paper.id in research_ids):
        inst_list.append("Research")
    elif( paper.id in case_ids):
        inst_list.append("Case Study")

    inst = Orange.data.Instance(domain, inst_list)

    paper_table.append(inst)

class SimpleTreeLearnerSetProb():
    """
    Orange.classification.tree.SimpleTreeLearner which sets the skip_prob
    so that on average a square root of the attributes will be 
    randomly choosen for each split.
    """
    def __init__(self, wrapped):
        self.wrapped = wrapped

    def __call__(self, examples, weight=0):
        self.wrapped.skip_prob = 1-len(examples.domain.attributes)**0.5/len(examples.domain.attributes)
        return self.wrapped(examples)



tree = Orange.classification.tree.TreeLearner(min_instances=5, measure="gainRatio")
rf_def = Orange.ensemble.forest.RandomForestLearner(trees=50, base_learner=tree, name="for_gain")

#random forests with simple trees - simple trees do random attribute selection by themselves
st = Orange.classification.tree.SimpleTreeLearner(min_instances=5)
stp = SimpleTreeLearnerSetProb(st)
rf_simple = Orange.ensemble.forest.RandomForestLearner(learner=stp, trees=50, name="for_simp")

learners = [ rf_def, rf_simple ]



print "--------------------3 Fold Cross Validation------------------------"

results = Orange.evaluation.testing.cross_validation(learners, paper_table, folds=3)
print "Learner  CA     Brier  AUC"
for i in range(len(learners)):
    print "%-8s %5.3f  %5.3f  %5.3f" % (learners[i].name, \
    Orange.evaluation.scoring.CA(results)[i], 
    Orange.evaluation.scoring.Brier_score(results)[i],
    Orange.evaluation.scoring.AUC(results)[i])

print "Storing tree learned from data"

import cPickle

tree = rf_simple( paper_table)

with open("paper_types.model",'wb') as f:
    cPickle.dump(tree, f)
