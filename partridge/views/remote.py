"""Accept remote URL as a paper file and download it """

import os
import uuid

from urllib2 import urlopen

from flask import current_app, render_template, request, jsonify

from partridge.tools.paperstore import PaperParser

def scan_url( the_url=None ):
    """Scan the URL for papers to download"""
    
    return render_template("remote_form.html")
    

def download_papers():

    if "url" in request.form:
        
        return do_scan( request.form['url'])
    elif "download_url" in request.form:
         url = request.form['download_url']

         try:
            download_paper( url )
            return jsonify({"status" : "ok"})
         except Exception as e:
            return jsonify({"status" : "error", "message" : str(e)})

def download_paper( url ):
    """Download the paper at URL and save to uploads folder"""

    destdir = current_app.config['PAPER_UPLOAD_DIR']

    u = urlopen( url )
    headers = u.info()
    type = headers['Content-type']

    if type.startswith("text/xml"):
        ext = ".xml"
    elif type.startswith("application/pdf"):
        ext = ".pdf"

    else:
        raise Exception("URL is not a supported content type")

    with open(os.path.join(destdir,  str(uuid.uuid4()) + ext), 'wb') as f:
        f.write(u.read())

    u.close()



def do_scan( url ):
    """Do the URL scan on the given site and get some json back.
    """

    #run a load of checks on the URL - it might be a paper


    u = urlopen( url )

    #get the headers
    headers = u.info()
    type = headers['Content-type']
    
    
    #get content type see if HTML, XML etc
    if type.startswith("text/html"):
        print "Its a page"
    elif type.startswith("text/xml"):
        
        p = PaperParser()
        p.parseFileObject( u )
        
        u.close()

        return render_template("remote_download.html", the_url=url,
            filetype="xml", paper_title=p.extractTitle(),
            authors=p.extractAuthors(),
            abstract=p.extractAbstract())


    elif type.startswith("application/pdf"):
        u.close()
        return render_template("remote_download.html", the_url=url,
        filetype="pdf")

    else:
        return render_template("remote_download.html", the_url=url,
            filetype="invalid")
