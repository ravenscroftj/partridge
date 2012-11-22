'''
Partridge database bootstrap module

This module loads all the SQL utilities that are needed to power Partridge's database.

The methdology behind it is loosely based on the pattern available here:
http://flask.pocoo.org/docs/patterns/sqlalchemy/

@author James Ravenscroft

'''
from pkgutil import walk_packages

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from config import config


engine = None

db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))

driver = config.database['driver']

if(driver == "sqlite"):
  path = config.database['path']
  connectionstring = "sqlite:////%s" % path

engine = create_engine(connectionstring, convert_unicode=True)

Base = declarative_base()
Base.query = db_session.query_property()

def initialise():
  '''Create all tables in the table. 
  
  This should be called after all models are imported
  '''
  Base.metadata.create_all(bind=engine)

def find_all_models():
  '''find all data model submodules and import them

  This function uses some python magic to find modules in the dbobj package 
  import them into the runtime. This allows all data models to be detected and
  installed.
  '''
  
  import dbobj
  
  for finder, name, ispkg in walk_packages(dbobj.__path__, dbobj.__name__ + '.'):
    
    loader = finder.find_module(name)

    if loader is not None:
      print "Loading %s " % name
      print loader.load_module(name)

