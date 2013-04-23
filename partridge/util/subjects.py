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

from collections import Counter

app = Flask(__name__)
app.config.update(config)

db.app = app
db.init_app(app)

corescs = C_ABRV.keys()

paper_root = "/home/james/dissertation/papers"

labels = {
"plos_maths" : "Mathematics", 
"plos_compsci" : "Information Technology",
"plos_physics" : "Physics"
}








def process_file( file ):
    """Process a paper file in the queue"""

    if file.endswith("_split.xml"):
        print "Found a paper %s" % file
        parse_paper( file )

    elif file.endswith(".xml"):
        print "Found an unsplit paper"

        fname,ext = os.path.splitext(file)

        splitfile = fname + "_split" + ext

        if os.path.exists(splitfile):
            print "Split file exists for this paper"
        else:
            s = SentenceSplitter()
            s.split(file, splitfile)

            parse_paper( splitfile)


if __name__ == "__main__":

    papers = []

    p = Pool()

    for root,dirs,files in os.walk(paper_root):
        p.map( process_file, [os.path.join(root,file) for file in files])

logging.basicConfig(level=logging.INFO)

