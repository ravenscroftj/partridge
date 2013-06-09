from flask.views import View
from flask import Blueprint, render_template,request

#register blueprint
frontend = Blueprint('frontend', __name__)


@frontend.route("/")
def index():
    '''Index view shows the front page for partridge
    '''
    return render_template("index.html")


