'''
Global configuration module for Partridge

'''
import os
import json
import flask


config = flask.Config(root_path=os.path.dirname(os.path.join("../../", __file__)), defaults={})

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
              
