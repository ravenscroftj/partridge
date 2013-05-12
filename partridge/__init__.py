import sys
import logging
import threading

from optparse import OptionParser
from flask import Config,Flask

from partridge.config import config
from partridge.models import db

from partridge.util.paperconv import PaperConverter, FileConverter


def create_app( config ):
    """Register app object and return to caller"""
    app = Flask(__name__)

    app.config.update(config)

    #load views model lazily
    import views
    import views.upload
    import views.paper
    import views.query
    import views.remote
    import views.queue

    app.url_map.converters["paper"] = PaperConverter
    app.url_map.converters["file"] = FileConverter

    app.add_url_rule("/",view_func = views.index)
    app.add_url_rule("/query", view_func = views.query.query)

    app.add_url_rule("/queue", view_func = views.queue.show)

    app.add_url_rule("/upload", methods=['GET','POST'], 
        view_func = views.upload.upload)

    app.add_url_rule("/remote", methods=['GET'],
        view_func = views.remote.scan_url)

    app.add_url_rule("/remote", methods=['POST'],
        view_func = views.remote.download_papers)

    app.add_url_rule("/bookmarklet", view_func = views.remote.bookmarklet)

    app.add_url_rule("/paper/<paper:the_paper>", 
        view_func=views.paper.paper_profile)

    app.add_url_rule("/file/<file:the_file>",
        view_func=views.paper.paper_file)

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

    parser.add_option("--paperdaemon", dest="paperdaemon", action="store_true",
        help="If set, runs only paper daemon and not a webserver")

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

    logLevel = logging.INFO

    if(opts.debug):
        print "Debug mode is active..."
        logLevel = logging.DEBUG

    if(opts.initdb):
        print "Initialising database tables..."
        db.create_all()
        
        
    #set up logger
    logging.basicConfig(level=logLevel, format="%(asctime)s - %(levelname)s - %(name)s:%(message)s")
    from partridge.preprocessor import create_daemon
    #set up paper preprocessor
    pdaemon =  create_daemon( config )

    if(config['PP_LOCAL_WORKER']):
        logging.info("Setting up local worker")
        from partridge.preprocessor.client import create_client

        clientevt = threading.Event()
        pclient = create_client( config, clientevt )

    if not opts.paperdaemon:
        app.debug = opts.debug
        try:
            app.run(host="0.0.0.0", port=int(opts.port))
        except KeyboardInterrupt as e:
            logging.info("Interrupted by user...")

    else:
        try:
            while 1:
                raw_input()
        except KeyboardInterrupt as e:
            logging.info("Interrupted by user...")

        
    if(config['PP_LOCAL_WORKER']):
        logging.info("Waiting for client to finish work...")
        clientevt.set()
        pclient.join()

    
    logging.info("Shutting down paper daemon...")
    pdaemon.stop()


