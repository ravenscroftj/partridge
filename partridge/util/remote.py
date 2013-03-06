""" Set of utility functions for the remote paper downloader
"""
import os
import uuid
from partridge.tools.paperstore import PaperParser

from HTMLParser import HTMLParser
from flask import render_template

def download_paper( url, destdir ):
    """Download the paper at URL and save to uploads folder"""

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


def paper_preview( url, file_object ):
    """Render a paper preview from a filelike object
    """
    
    p = PaperParser()
    p.parseFileObject( file_object )

    return render_template("remote_download.html", the_url=url,
        filetype="xml", paper_title=p.extractTitle(),
        authors=p.extractAuthors(),
        abstract=p.extractAbstract())


class PlosScanner(HTMLParser):
    
    link = ""
    
    def handle_starttag(self, tag, attrs):
        if tag == "a":
            
            title = ""
            href = ""

            for key, value in attrs:
               if key == "title": title = value
               if key == "href" : href = value
                
            if title == "Download article XML":
                self.link = href


def find_paper_plos_page( html ):
    """Scan the input plos HTML and return a paper URL if possible"""
    
    p = PlosScanner()
    p.feed(html)

    return p.link
    
