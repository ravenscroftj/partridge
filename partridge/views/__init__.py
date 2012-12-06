from flask.views import View
from flask import render_template

def index():
    '''Index view shows the front page for partridge
    '''
    return render_template("index.html")
