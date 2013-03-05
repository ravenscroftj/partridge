"""
A small utility that can be used to guess a paper's type using the forest model

"""

import os
import sys
import cPickle
import Orange

from partridge.config import config
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy

from partridge.models import db
from partridge.models.doc import Paper

app = Flask(__name__)
app.config.update(config)

db.app = app
db.init_app(app)

PAPER_TYPE_MODEL_PATH = os.path.join(config['MODELS_DIR'], "paper_types.model")

FEATURES = ['Bac', 'Mot', 'Met']

class PaperClassifier:

    def __init__(self):

        with open(PAPER_TYPE_MODEL_PATH, 'rb') as f:
            self.classifier = cPickle.load(f)

    def get_paper_by_id(self, id):
        return Paper.query.filter(Paper.id == id).first()


    def classify_paper_id( self, id ):
        return self.classify_paper(self.get_paper_by_id(paper))

    def classify_paper( self, paper ):
        inst = self.instance_from_paper(paper)
        return self.classifier( inst )
    
    def instance_from_paper( self, paper ):
        inst_list = []
        sentdist = paper.sentenceDistribution(True)

        for feature in FEATURES:
            inst_list.append( sentdist[feature] * 100 / len(paper.sentences) )

        inst_list.append("")

        return Orange.data.Instance(self.classifier.domain, inst_list)


if __name__ == "__main__":

    c = PaperClassifier()
    p = c.get_paper_by_id(sys.argv[1])
    
    print p.title
    for author in p.authors:
        print "\t\t" + author.surname
    
    print "Predicted Class:" + str( c.classify_paper(p) )
