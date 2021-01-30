"""
A small utility that can be used to guess a paper's type using the forest model

"""

import os
import sys
import pickle
import Orange


from optparse import OptionParser

from partridge.config import config
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from partridge.models import db
from partridge.models.doc import Paper, C_ABRV

from partridge.tools.paperstore import PaperParser

PAPER_TYPE_MODEL_PATH = os.path.join(config['MODELS_DIR'], "paper_types.model")

FEATURES = C_ABRV.keys()

class PaperClassifier:

    # def __init__(self):

    #     with open(PAPER_TYPE_MODEL_PATH, 'rb') as f:
    #         self.classifier = pickle.load(f)

    def get_paper_by_id(self, id):
        return Paper.query.filter(Paper.id == id).first()


    def classify_paper_id( self, id ):
        return self.classify_paper(self.get_paper_by_id(id))

    def classify_paper( self, paper ):
        #inst = self.instance_from_paper(paper)

        return "Unknown" #return self.classifier( inst )
    
    def instance_from_paper( self, paper ):
        inst_list = []
        sentdist = paper.sentenceDistribution(True)

        for feature in FEATURES:
            inst_list.append( sentdist[feature] * 100 / len(paper.sentences) )

        inst_list.append("")

        return Orange.data.Instance(self.classifier.domain, inst_list)

class RawPaperClassifier(PaperClassifier):
    """Classify paper file rather than using db connection"""

    def classify_paper(self, filename):
        """Read a paper, find all sentences and then classify"""

        p = PaperParser()
        p.parsePaper(filename)

        types = {x:0 for x in FEATURES}

        sentenceCount = 0

        for _, annotype in p.extractSentences():
            sentenceCount += 1
            types[annotype] += 1


        inst_list = []

        for feature in FEATURES:
            inst_list.append( types[feature] * 100 / sentenceCount)

        inst_list.append("")

        inst = Orange.data.Instance(self.classifier.domain, inst_list)

        return self.classifier(inst)

      




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
        print ("ignoring ID arguments and retrieving all papers")
        q = Paper.query
    else:
        print (f"Retrieving papers with IDs in {args}")
        q= Paper.query.filter(Paper.id.in_(args))

    offset = 0
    limit = 50


    while q.offset(offset).limit(limit).count() > 0:

        print ("Downloading batch of {limit} papers...")

        for p in q.offset(offset).limit(limit).all():
            
            print (p.title)
            for author in p.authors:
                print ("\t\t" + author.surname)

            cls = str(c.classify_paper(p))
            
            print ("Predicted Class:" + cls)

            print ("Saving paper type in database")
            p.type = cls
            db.session.merge(p)
        
        #commit the database session at the end of the run
        db.session.commit()

        offset += limit
