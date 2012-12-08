from flask.views import View
from flask import render_template,request

def index():
    '''Index view shows the front page for partridge
    '''
    return render_template("index.html")

def query():
    '''Display the query form and then show results if a query is provided
    '''

    searchterms = request.args.get('q','')

    if(searchterms != ''):
        pass
        #TODO Display search results
    else:
        return render_template("query.html")
