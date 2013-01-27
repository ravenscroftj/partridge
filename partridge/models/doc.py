from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship, backref

from partridge.models import db

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

#-----------------------------------------------------------------------------

class Author( db.Model ):
    
    __tablename__ = "authors"

    id = Column(Integer, primary_key=True)
    surname = Column(String(50))
    forenames = Column(String(50))

#-----------------------------------------------------------------------------


