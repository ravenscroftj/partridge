"""View stats and info for a known paper in the database"""
import mimetypes
from flask import render_template, current_app, Response

def paper_profile(the_paper):
    """Given a paper object, render a profile page""" 
    
    return render_template("paperprofile.html", paper=the_paper)


def paper_file( the_file ):
    r  = Response()
    r.mimetype=mimetypes.guess_type(the_file.path)[0]
    with open(the_file.path,'rb') as f:
        r.data = f.read()
    return r
