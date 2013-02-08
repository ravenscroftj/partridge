from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship, backref

from collections import Counter

from partridge.models import db

#list of coresc concept abreviations and full labels
C_ABRV = {
"Hyp" : "Hypothesis",
"Obj" : "Object",
"Res" : "Result",
"Goa" : "Goal",
"Mot" : "Motivation",
"Met" : "Method",
"Bac" : "Background",
"Exp" : "Experiment",
"Mod" : "Model",
"Obs" : "Observation",
"Con" : "Conclusion"
}

#-----------------------------------------------------------------------------

paper_authors = db.Table('paper_authors',
    db.Column('paper_id', db.Integer, db.ForeignKey('papers.id')),
    db.Column('author_id', db.Integer, db.ForeignKey('authors.id')),
    db.Column('primary_author', db.Boolean)
)

#-----------------------------------------------------------------------------

class Paper( db.Model ):

  __tablename__ = "papers"

  id = Column(Integer, primary_key=True)
  title = Column(String(250)) 
  authors = relationship("Author", secondary=paper_authors, backref="papers")
  abstract = Column(Text())

  def sentenceDistribution(self, returnCounter=False):
    totalSentences = len(self.sentences)

    count = Counter()

    for sent in self.sentences:
        count[sent.coresc] += 1

    if returnCounter:
        return count

    percentages = []

    for label, num in count.items():
        percentages.append( (C_ABRV[label], num * 100 / totalSentences) )
    
    return percentages
        

#-----------------------------------------------------------------------------

class Sentence( db.Model ):
  
  __tablename__ = "sentences"

  id     = Column(Integer, primary_key=True)
  text   = Column(Text)
  coresc = Column(String(25))
  paper_id = Column(Integer, db.ForeignKey('papers.id'))
  paper  = relationship("Paper", backref=backref('sentences', order_by=id),
    primaryjoin=(paper_id==Paper.id) )

#-----------------------------------------------------------------------------

class PaperFile( db.Model ):

  __tablename__ = "paper_files"

  id       = Column(Integer, primary_key=True)
  path     = Column(String(100))
  type     = Column(String(10))
  paper_id = Column(Integer, db.ForeignKey('papers.id'))
  paper    = relationship("Paper", backref=backref('files', order_by=id),
  primaryjoin=(paper_id==Paper.id))
  
  @property
  def basename(self):
    import os
    return os.path.basename(self.path)

  @property
  def contentType(self):
    """Guess what sort of file this is"""

    if self.path.endswith(".pdf"):
        return "Original PDF format"

    if "final" in self.path:
        return "Final annotated XML file"

    else:
        return "Initial XML version of the paper"
#-----------------------------------------------------------------------------

class Author( db.Model ):
    
    __tablename__ = "authors"

    id = Column(Integer, primary_key=True)
    surname = Column(String(50))
    forenames = Column(String(50))

#-----------------------------------------------------------------------------


