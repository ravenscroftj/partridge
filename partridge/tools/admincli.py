"""
This module provides a CLI for partridge administration

"""

import sys
from optparse import OptionParser
from partridge import create_app
from flask import Config


import codecs

import xml.dom.minidom

from partridge.config import config
from partridge.models import db
from partridge.models.doc import Paper, Sentence, Author 


class PaperManager(object):

    def parse_options(self, args):
        fname = "oper_%s" % args[0]

        if hasattr(self, fname) and callable(getattr(self,fname)):
            getattr(self,fname)(*args[1:])
        else:
            print "No such operation " + args[0]

    def oper_delete(self, id):
        paper = Paper.query.filter(Paper.id == id).first()


        if paper == None:
            print "No paper with id %s " % id
            return

	msg = u"Delete '%s' by %s? [Y/n] " % (paper.title, u" and ".join([ (a.forenames + u" " + a.surname) 
						for a in paper.authors]))

	message = codecs.encode(msg, 'ascii', 'ignore')

        response = raw_input(message)

        print " '%s' " % response

        if(response.strip() == "Y"):
            print "Deleting paper from database..."
            db.session.delete(paper)
            db.session.commit()
        else:
            print "Response was not Y, no action will be taken"



def main():
    optparser = OptionParser()
    
    optparser.add_option("-c", "--configfile", dest="config",
        default="", help="Override the path to the config file to load.")

    opts,args = optparser.parse_args(sys.argv)

    if(opts.config != ""):
        try:
            config.from_pyfile(opts.config)
        except IOError:
                print "Could not find any configuration files. Exiting."
                sys.exit(0)

    create_app(config)

    if(len(args) < 2):
        print "Invalid arguments"
        sys.exit(0)

    if (args[1] == "paper") and len(args) > 2:
        #expect the next argument to be the operation
        p = PaperManager()
        p.parse_options(args[2:])
    
    else:
        print "Invalid arguments."
        



if __name__ == "__main__":
    main()

