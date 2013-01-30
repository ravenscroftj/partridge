"""View stats and info for a known paper in the database"""

from flask import render_template, current_app

def paper_profile(the_paper):
    """Given a paper object, render a profile page""" 
    
    return render_template("paperprofile.html", paper=the_paper)

