import sys

from optparse import OptionParser
from flask import Config

from web import create_app
from models import db


def run():
    
    #set up an option parser
    parser = OptionParser()

    parser.add_option("-v", "--verbose", dest="verbose", action="store_true",
        help="Make the server provide more verbose logging to the console")

    parser.add_option("-p", "--port", dest="port", default="5000",
        help="Set the port that partridge will server web pages on")

    parser.add_option("-c", "--configfile", dest="config", default="",
        help="Override the path to the config file to load.")

    parser.add_option("-d", "--debug", dest="debug", action="store_true",
        help="Store true if the server should run in debug mode")

    parser.add_option("--initdb", action="store_true",dest="initdb",
        help="Initialise the patridge database and create tables")

    opts,args = parser.parse_args(sys.argv)

    try:
        config = Config({})
        config.from_pyfile(opts.config)
    except IOError:
        try:
            config.from_pyfile("partridge.cfg")
        except:
            print "Could not find any configuration files. Exiting."
            sys.exit(0)

    app = create_app( config )

    if(opts.debug):
        print "Debug mode is active..."

    app.debug = opts.debug
    app.run(host="0.0.0.0", port=int(opts.port))
