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

PAPER_TYPES = ["Review", "Case Study", "Research"]

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
  doi   = Column(String(50))
  title = Column(String(250)) 
  authors = relationship("Author", secondary=paper_authors, backref="papers")
  abstract = Column(Text())
  type = Column(String(25))


  def json(self):
      return {
              "title" : self.title,
              "doi"   : self.doi,
              "authors" : [a.json() for a in self.authors],
              "abstract" : self.abstract,
              "files" : [f.json() for f in self.files]
              } 

  def sentenceDistribution(self, returnCounter=False):
    totalSentences = len(self.sentences)

    count = Counter({x:0 for x in C_ABRV})

    for sent in self.sentences:
        count[sent.coresc] += 1

    if returnCounter:
        return count

    percentages = []

    for label, num in sorted(count.items(), key=lambda x: x[0]):
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

  def json(self):
      from flask import url_for
      return {
                "name" : self.basename,
                "type" : self.contentType,
                "url"  : url_for('frontend.paper_file', the_file=self, _external=True)
              }

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
    surname = Column(String(250))
    forenames = Column(String(250))

    def json(self):
        return {"id" : self.id, "surname" : self.surname, "forenames" : self.forenames}

#-----------------------------------------------------------------------------

class PaperWatcher( db.Model ) :

    __tablename__ = "paper_watchers"

    filename = Column(String(50), primary_key=True)
    email = Column(String(50))
    
