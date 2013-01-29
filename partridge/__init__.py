import sys
import logging

from optparse import OptionParser
from flask import Config,Flask

from partridge.config import config
from partridge.models import db


def create_app( config ):
    """Register app object and return to caller"""
    app = Flask(__name__)

    app.config.update(config)

    #load views model lazily
    import views
    import views.upload

    app.add_url_rule("/",view_func = views.index)
    app.add_url_rule("/query", view_func = views.query)
    app.add_url_rule("/upload", view_func = views.upload.upload)
    db.app = app
    db.init_app(app)
    return app

def run():
    
    #set up an option parser
    parser = OptionParser()

    parser.add_option("-v", "--verbose", dest="verbose", action="store_true",
        help="Make the server provide more verbose logging to the console")

    parser.add_option("-p", "--port", dest="port", default="5000",
        help="Set the port that partridge will server web pages on")

    parser.add_option("-c", "--configfile", dest="config",
        default="", help="Override the path to the config file to load.")

    parser.add_option("-d", "--debug", dest="debug", action="store_true",
        help="Store true if the server should run in debug mode")

    parser.add_option("--initdb", action="store_true",dest="initdb",
        help="Initialise the patridge database and create tables")

    opts,args = parser.parse_args(sys.argv)

    if(opts.config != ""):
        try:
            config.from_pyfile(opts.config)
        except IOError:
                print "Could not find any configuration files. Exiting."
                sys.exit(0)

    app = create_app( config )

    if(opts.debug):
        print "Debug mode is active..."

    if(opts.initdb):
        print "Initialising database tables..."
        db.create_all()

    from partridge.preprocessor import create_daemon
    #set up paper preprocessor
    pdaemon =  create_daemon( config )
    pdaemon.start()

    app.debug = opts.debug
    app.run(host="0.0.0.0", port=int(opts.port))

    pdaemon.stop()
