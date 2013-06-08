from __future__ import division

import os
import csv
from partridge.config import config
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy

from partridge.models import db
from partridge.models.doc import Paper, PaperFile, Sentence, C_ABRV


TYPE_DIRS = {
    "Review"     : "/home/james/dissertation/papers_for_type/review",
    "Research"   : "/home/james/dissertation/papers_for_type/research",
    "Case Study" : "/home/james/dissertation/papers_for_type/case", 
    "Essay"      : "/home/james/dissertation/papers_for_type/essay",
    "Opinion"    : "/home/james/dissertation/papers_for_type/opinion",
    "Perspective": "/home/james/dissertation/papers_for_type/perspective",
    "Viewpoint"  : "/home/james/dissertation/papers_for_type/viewpoints",
}

FEATURES = C_ABRV.keys()

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


if __name__ == "__main__":

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


    with open("output.tab","w") as f:
        csvwriter = csv.writer(f, delimiter="\t",quotechar='|',
        quoting=csv.QUOTE_MINIMAL)

        #write the metadata
        csvwriter.writerow(FEATURES + ["type"])

        #write the types for the content
        csvwriter.writerow( (["c"] * len(FEATURES)) + ['d'])

        #write the class identifier
        csvwriter.writerow( ([''] * len(FEATURES)) + ['class'])

        offset = 0
        limit = 50

        q = Paper.query.filter(Paper.id.in_(all_ids))

        while q.offset(offset).limit(limit).count() > 0:

            print "Downloading batch of %d papers..." % limit

            #write the data itself
            for paper in q.offset(offset).limit(limit).all():
                row = []
                sentdist = paper.sentenceDistribution(True)
                for coresc in FEATURES:
                    row.append(sentdist[coresc] * 100 / len(paper.sentences))

                for type in types:
                    if paper.id in types[type]:
                        row.append(type)
                        break

                #write the row
                csvwriter.writerow(row)

            offset += limit

    print "Table saved"
