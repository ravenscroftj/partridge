from flask.views import View
from flask import render_template,request


from partridge.models import db
from partridge.models.doc import Paper

from sqlalchemy import func

def index():
    '''Index view shows the front page for partridge
    '''
    return render_template("index.html")

def query():
    '''Display the query form and then show results if a query is provided
    '''

    searchterms = request.args.get('q','')

    r = db.session.query(func.count(Paper.id))

    papercount = r.first()[0]

    if(searchterms != ''):
        pass
        #TODO Display search results
    else:
        return render_template("query.html", paper_count=papercount)
