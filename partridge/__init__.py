import sys

from optparse import OptionParser
from web import app,serve

def run():
    
    #set up an option parser
    parser = OptionParser()

    parser.add_option("-v", "--verbose", dest="verbose", action="store_true",
        help="Make the server provide more verbose logging to the console")

    parser.add_option("-p", dest="port", default=5000,
        help="Set the port that partridge will server web pages on")

    parser.add_option("-d", "--debug", dest="debug", action="store_true",
        help="Store true if the server should run in debug mode")

    opts,args = parser.parse_args(sys.argv)

    if(opts.debug):
        print "Debug mode is active..."
    
    serve(opts.port, opts.debug)
