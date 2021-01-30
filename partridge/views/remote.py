"""Accept remote URL as a paper file and download it """

import os
import re
import requests

from datetime import datetime

from urllib.parse import urlparse, urlunparse
#from urllib2 import urlopen

#import urlparse

from flask import current_app as app, render_template, request, jsonify, make_response

from partridge.views import frontend

from partridge.util.remote import download_paper, paper_preview, \
    find_paper_plos_page

from partridge.models import db
from partridge.models.doc import PaperWatcher

PMC_OSI = "http://www.pubmedcentral.gov/oai/oai.cgi?verb=GetRecord&identifier=oai:pubmedcentral.nih.gov:%s&metadataPrefix=pmc"


@frontend.route("/remote", methods=['GET'])
def scan_url(the_url=None):
    """Scan the URL for papers to download"""

    return render_template("remote_form.html")


@frontend.route("/bookmarklet")
def bookmarklet():
    """Serve up the bookmarklet script"""
    response = make_response(render_template("bookmarklet.js"))
    response.headers['Content-type'] = "text/javascript"
    return response


@frontend.route("/remote", methods=['POST'])
def download_papers():

    if "url" in request.form:
        return do_scan(request.form['url'])

    elif "download_url" in request.form:
        from partridge.preprocessor.service import annotate_paper

        url = request.form['download_url']

        now = datetime.now()
        destdir = os.path.join(os.environ.get(
            "PARTRIDGE_UPLOAD_PREFIX", "uploads"), now.strftime("%Y/%m/%d"))
        paper = download_paper(url, destdir)

        annotate_paper.send(paper)

        try:
            app.logger.info("Downloading paper at %s", url)

            if "email" in request.form:
                app.logger.info("Registering watcher for paper at email %s",
                                request.form['email'])

                watcher = PaperWatcher()
                watcher.email = request.form['email']
                watcher.filename = paper

                db.session.add(watcher)
                db.session.commit()

            return jsonify({"status": "ok"})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)})


def do_scan(url):
    """Do the URL scan on the given site and get some json back.
    """

    # run a load of checks on the URL - it might be a paper

    if(url.find("ncbi.nlm.nih.gov/pmc/articles/") > -1):

        # get paper by PMC
        m = re.search("PMC([0-9]+)", url)

        if m != None:
            id = m.group(1)

            url = PMC_OSI % id

    try:
        r = requests.get(url)
    except:
        return "Invalid URL. Try again!"

    # get the headers
    content_type = r.headers['Content-type']

    # get content type see if HTML, XML etc
    if content_type.startswith("text/html"):

        # see if its a PLOS page and whether we can harvest links
        m = re.search

        if(re.search("https?://www\.(plos.+)\.org/article/info", url) != None):
            # try extracting links to XML doc
            path = find_paper_plos_page(u.read())
            u.close()

            if(path != ""):

                n = urlparse(url)
                newurl = (n.scheme, n.netloc, path,
                          n.params, n.query, n.fragment)

                newurl = urlunparse(newurl)
                r = requests.get(newurl)

                output = paper_preview(newurl, r.text)

                return output

        # -----Otherwise if we got to this stage, no HTML handler is set up

        return render_template("remote_download.html", the_url=url,
                               filetype="invalid")

    elif content_type.startswith("text/xml") or content_type.startswith("application/xml"):
        output = paper_preview(url, r.text)
        return output

    elif content_type.startswith("application/pdf"):
        return render_template("remote_download.html", the_url=url,
                               filetype="pdf")

    else:
        return render_template("remote_download.html", the_url=url,
                               filetype="invalid")
