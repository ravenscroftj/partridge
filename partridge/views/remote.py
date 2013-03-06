"""Accept remote URL as a paper file and download it """

import os
import re

from urllib2 import urlopen

import urlparse

from flask import current_app, render_template, request, jsonify, make_response

from partridge.util.remote import download_paper, paper_preview, \
find_paper_plos_page

PMC_OSI = "http://www.pubmedcentral.gov/oai/oai.cgi?verb=GetRecord&identifier=oai:pubmedcentral.nih.gov:%s&metadataPrefix=pmc"

def scan_url( the_url=None ):
    """Scan the URL for papers to download"""
    
    return render_template("remote_form.html")

def bookmarklet():
    """Serve up the bookmarklet script"""
    response = make_response(render_template("bookmarklet.js"))
    response.headers['Content-type'] = "text/javascript"
    return response
    

def download_papers():

    if "url" in request.form:
        return do_scan( request.form['url'])

    elif "download_url" in request.form:
         url = request.form['download_url']

         try:
            download_paper( url, current_app.config['PAPER_UPLOAD_DIR'] )
            return jsonify({"status" : "ok"})
         except Exception as e:
            return jsonify({"status" : "error", "message" : str(e)})

def do_scan( url ):
    """Do the URL scan on the given site and get some json back.
    """

    #run a load of checks on the URL - it might be a paper


    if( url.find("ncbi.nlm.nih.gov/pmc/articles/") > -1):
       
        #get paper by PMC
        m = re.search("PMC([0-9]+)", url)
        
        if m != None:
            id = m.group(1)

            url = PMC_OSI % id

    print url

    try:
        u = urlopen( url )
    except:
        return "Invalid URL. Try again!"

    #get the headers
    headers = u.info()
    type = headers['Content-type']
    
    
    #get content type see if HTML, XML etc
    if type.startswith("text/html"):

        #see if its a PLOS page and whether we can harvest links

        if( url.find("www.plosone.org/article/info") > -1):
            #try extracting links to XML doc
            path = find_paper_plos_page( u.read() )
            u.close()

            if(path != ""): 

                n = urlparse.urlparse( url )
                newurl = (n.scheme, n.netloc, path, n.params, n.query, n.fragment)

                newurl = urlparse.urlunparse(newurl)
                u = urlopen( newurl )

                output = paper_preview( newurl, u )
                u.close()
                
                return output



        ##-----Otherwise if we got to this stage, no HTML handler is set up
        
        return render_template("remote_download.html", the_url=url,
                filetype="invalid")


    elif type.startswith("text/xml"):
       output = paper_preview( url, u ) 
       u.close()
       return output


    elif type.startswith("application/pdf"):
        u.close()
        return render_template("remote_download.html", the_url=url,
        filetype="pdf")

    else:
        return render_template("remote_download.html", the_url=url,
            filetype="invalid")
