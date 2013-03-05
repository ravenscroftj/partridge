"""
A small utility that can be used to guess a paper's type using the forest model

"""

import os
import sys
import cPickle
import Orange


from optparse import OptionParser

from partridge.config import config
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy

from partridge.models import db
from partridge.models.doc import Paper, C_ABRV

PAPER_TYPE_MODEL_PATH = os.path.join(config['MODELS_DIR'], "paper_types.model")

FEATURES = C_ABRV.keys()

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


    app = Flask(__name__)
    app.config.update(config)

    db.app = app
    db.init_app(app)


    parser = OptionParser()

    parser.add_option("-a", "--all", action="store_true", dest="all",
        help="If is set, updates all unknown papers in database")


    options,args = parser.parse_args()

    c = PaperClassifier()

    if(options.all):
        print "ignoring ID arguments and retrieving all papers"
        papers = Paper.query.all()
    else:
        print "Retrieving papers with IDs in %s" % args
        papers = Paper.query.filter(Paper.id.in_(args)).all()

    for p in papers:

        if( p.type != None ):
            print "Skipping paper %s" % p.title
            continue
        
        print p.title
        for author in p.authors:
            print "\t\t" + author.surname

        cls = str(c.classify_paper(p))
        
        print "Predicted Class:" + cls

        print "Saving paper type in database"
        p.type = cls
        db.session.merge(p)
    
    #commit the database session at the end of the run
    db.session.commit()

