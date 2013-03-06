""" Retrieve papers from plosONE


"""
import sys
from optparse import OptionParser
import os
import json
from urllib2 import urlopen, quote

searchUrl = 'http://api.plos.org/search?'
apiKey = "dCFoAOqdkBUcOI2"
dlURL = "http://%s/article/fetchObjectAttachment.action?uri=info%%3Adoi%%2F%s&representation=XML"



def downloadPaper( paper_id, folder ):
    '''Download the paper with given paper_id as XML and store in folder.'''

    outfilename = os.path.join(folder, paper_id.split("/")[1] + ".xml")

    bits = paper_id.split("/")

    if(len(bits) > 2):
        paper_id = bits[0] + "/" + bits[1]

    journals = {
        "pone" : "www.plosone.org",
        "pcbi" : "www.ploscompbiol.org"
    }

    try:
        journal = journals[paper_id.split("/")[1].split(".")[1]]
    except:
        journal = journals["pone"]

    url = dlURL % (journal, paper_id)

    
    if(os.path.isfile(outfilename)):
        print "Skipping %s, already downloaded..." % url
    else:
        print "Downloading %s..." % url
        print "Storing it at %s..." % outfilename

        u = urlopen( url )
        with open(outfilename, 'wb') as f:
                f.write(u.read())
        u.close()

def query( query_params ):
    '''Find papers using plos api and return as JSON model
    '''

    query = {
        "q" : "*:*",
        "api_key" : apiKey,
        "wt" : "json",
        "fq" : quote('doc_type:full AND article_type:Opinion'),
        }

    query = dict( query.items() + query_params.items() )


    url = searchUrl

    for part in query:
        url += '%s%s=%s' % ('&' if url is not searchUrl else '',part,query[part])

    print "Requesting %s" % url

    response = json.load(urlopen(url))

    return response['response']


def main():
    '''Main script entrypoint for plosget
    '''
    o = OptionParser()

    o.add_option("-q", "--query", dest="query", default="*:*",
        help="Main query, [default *:*]")

    o.add_option("--field-query", dest="fq", default="",
        help="Set field specific constraints such as paper type")

    o.add_option("-d", "--directory", dest="directory", 
        help = "Directory to save papers into",default="papers")

    o.add_option("-r", "--results", dest="results", default=10,
        help="Maximum number of papers to download, [MAX:100]")

    o.add_option("-s", "--start", dest="start", default=0,
        help="First row to return [default: 0]")

    o.add_option("-p", "--print", dest="p", action="store_true",
        help="If set, just print the result of the query and exit")
    
   
    opts, args = o.parse_args()

    query_parms = {}

    query_parms['rows'] = min( opts.results, 100)
    query_parms['start'] = opts.start
    query_parms['q'] = quote(opts.query)
    query_parms['fq'] = quote(opts.fq)

        
    
    response = query( query_parms )

    print "Found %d documents matching query" % response['numFound']


    for doc in response['docs']:
        if(opts.p):
            print doc
        else:
            downloadPaper( doc['id'], opts.directory )
    


#--------------------------------------------------------------------------------

if __name__ == "__main__":
    main()
