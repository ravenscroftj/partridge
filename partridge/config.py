'''
Global configuration module for Partridge

'''
import os
import json
import flask

class Config:
  
  def load(self, conffile):
    with open(conffile,'r') as f:
      config = json.load(f)

      for k in config.keys():
        self.__dict__[k] = config[k]


config = flask.Config({})

if( os.getenv("PARTRIDGE_CONF")):
    #try and load config from env directory
    config.from_envvar("PARTRIDGE_CONF")

for loc in (os.getcwd(), 
  os.path.expanduser("~/.config/"), 
  "/etc/"):
  
          try:
                source = os.path.join(loc,"partridge.cfg")
                config.from_pyfile(source)
          except IOError:
            pass
              
