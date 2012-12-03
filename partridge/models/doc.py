from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship, backref

from partridge.database import Base

#-----------------------------------------------------------------------------

class Paper( Base ):

  __tablename__ = "papers"

  id = Column(Integer, primary_key=True)
  title = Column(String) 

#-----------------------------------------------------------------------------

class Sentence( Base ):
  
  __tablename__ = "sentences"

  id     = Column(Integer, primary_key=True)
  text   = Column(String)
  coresc = Column(String)
  paper  = user = relationship("Paper", backref=backref('sentences', order_by=id))

#-----------------------------------------------------------------------------

class PaperFile( Base ):

  __tablename__ = "paper_files"

  id     = Column(Integer, primary_key=True)
  path   = Column(String)
  type   = Column(String)
  paper  = user = relationship("Paper", backref=backref('files', order_by=id))
