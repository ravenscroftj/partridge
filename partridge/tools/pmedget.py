""" Retrieve papers from Pubmed

"""
import sys
from optparse import OptionParser
import os
from urllib2 import urlopen

apiURL = """http://www.pubmedcentral.gov/oai/oai.cgi?verb=GetRecord&identifier=oai:pubmedcentral.nih.gov:%s&metadataPrefix=pmc"""

def downloadPaper( paper_id, folder):
    
    outfilename = os.path.join(folder, "pmc" + paper_id + ".xml")

    if (os.path.exists(outfilename)):
        print "Paper %s exists, skipping" % paper_id

    u = urlopen(apiURL % id)

    print "Downloading paper at %s" % ( apiURL % id) 
    
    with open (outfilename,'wb') as f:
        f.write(u.read())


if __name__ == "__main__":


    o = OptionParser()

    
    o.add_option("-d", "--directory", dest="directory", 
        help = "Directory to save papers into",default="papers")

    
    opts, args = o.parse_args()

    for id in args:

        if id.startswith("PMC"):
            id = id[3:]
        
        downloadPaper(id, opts.directory)
        
