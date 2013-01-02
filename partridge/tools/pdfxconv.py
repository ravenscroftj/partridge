#!/usr/bin/env python
'''
This script enables the conversion of a PDF document to XML recognised by Sapienta via pdfx

'''
import sys
import os
import logging

from optparse import OptionParser
from converter import PDFXConverter
from annotate import Annotator, RemoteAnnotator
from split import SentenceSplitter


def main():
    
    usage = "usage: %prog [options] file1.pdf [file2.pdf] "
    
    parser = OptionParser(usage=usage)
    parser.add_option("-s", "--split-sent", action="store_true", dest="split",
        help="If true, split sentences using NLTK sentence splitter")
    parser.add_option("-a", "--annotate", action="store_true", dest="annotate",
        help="If true, annotate the split XML with coreSC stuff")
    parser.add_option("-v", "--verbose", action="store_true", dest="verbose",
        help="If set, provides more verbose output")
    
    (options, args) = parser.parse_args()

    if(options.verbose):
        logging.basicConfig(level=logging.DEBUG)
        logging.debug("Verbose mode on.")

    if( len(args) < 1):
        parser.print_help()
        sys.exit(1)
 
    for infile in args:
        name,ext = os.path.splitext(infile)

        if not(os.path.exists(infile)):
            print "Input file %s does not exist" % infile
            continue

        outfile = name + ".xml"

        p = PDFXConverter()

        #annotation requires splitting
        if(options.annotate):
            options.split = True

                
        if(ext == ".pdf"):

            print "Converting %s" % infile
            
            p.convert(infile, outfile)
            split_infile = outfile
            
        elif( ext == ".xml"):
            print "No conversion needed on %s" % infile
            split_infile = infile

        else:
            print "Unrecognised format for file %s" % infile

        if(options.split):
            print "Splitting sentences in %s" % infile
            
            s = SentenceSplitter()
            s.split(split_infile, outfile)

            anno_infile = outfile

        if(options.annotate):
            a = RemoteAnnotator()

            #build annotated filename
            name,ext = os.path.splitext(anno_infile)
            outfile = name + "_annotated" + ext
            a.annotate( anno_infile, outfile )



if __name__ == "__main__":
    main()
