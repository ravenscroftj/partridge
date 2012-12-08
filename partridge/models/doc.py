from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship, backref

from partridge.models import db

#-----------------------------------------------------------------------------

class Paper( db.Model ):

  __tablename__ = "papers"

  id = Column(Integer, primary_key=True)
  title = Column(String) 

#-----------------------------------------------------------------------------

class Sentence( db.Model ):
  
  __tablename__ = "sentences"

  id     = Column(Integer, primary_key=True)
  text   = Column(String)
  coresc = Column(String)
  paper  = relationship("Paper", backref=backref('sentences', order_by=id))


#-----------------------------------------------------------------------------

paper_authors = db.Table('paper_authors',
    db.Column('paper_id', db.Integer, db.ForeignKey('papers.id')),
    db.Column('author_id', db.Integer, db.ForeignKey('authors.id')),
    db.Column('primary_author', db.Boolean)
)


#-----------------------------------------------------------------------------

class PaperFile( db.Model ):

  __tablename__ = "paper_files"

  id     = Column(Integer, primary_key=True)
  path   = Column(String)
  type   = Column(String)
  paper  = relationship("Paper", backref=backref('files', order_by=id))

#-----------------------------------------------------------------------------

class Author( db.Model ):
    
    __tablename__ = "authors"

    id = Column(Integer, primary_key=True)
    surname = Column(String)
    forenames = Column(String)

#-----------------------------------------------------------------------------


