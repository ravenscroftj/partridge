"""Accept remote URL as a paper file and download it """

import pycurl

from flask import current_app

def download_paper( the_url ):

    
    c = pycurl.Curl()
    c.setopt(pycurl.URL, the_url)
    c.setopt(pycurl.FOLLOWLOCATION, True)
    
    
    
    
    
    
    return "The url you gave me was %s " % the_url
