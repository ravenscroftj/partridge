""" Set of utility functions for the remote paper downloader
"""
import os
import uuid
import io
import requests

from partridge.tools.paperstore import PaperParser
from partridge.preprocessor import get_minio_client

#from urllib2 import urlopen
from html.parser import HTMLParser

from flask import render_template


def download_paper(url, destdir):
    """Download the paper at URL and save to uploads folder"""

    r = requests.get(url)
    type = r.headers['Content-type']

    print(f"Paper type: {type}")

    if "xml" in type:
        ext = ".xml"
    elif type.startswith("application/pdf"):
        ext = ".pdf"

    else:
        raise Exception("URL is not a supported content type")

    filename = str(uuid.uuid4()) + ext

    mc = get_minio_client()

    fullpath = os.path.join(destdir,  filename)

    mc.put_object(os.getenv("MINIO_BUCKET"), fullpath, io.BytesIO(
        r.content), len(r.content), r.headers['content-type'])

    return fullpath


def paper_preview(url, response_text):
    """Render a paper preview from a filelike object
    """

    p = PaperParser()
    p.parseString(response_text)

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
                if key == "title":
                    title = value
                if key == "href":
                    href = value

            if title == "Download article XML":
                self.link = href


def find_paper_plos_page(html):
    """Scan the input plos HTML and return a paper URL if possible"""

    p = PlosScanner()
    p.feed(html)

    return p.link
