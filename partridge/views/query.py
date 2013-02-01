"""Views related to querying partridge"""

from flask import render_template,request
from partridge.models import db
from partridge.models.doc import Paper, C_ABRV

from sqlalchemy import func

def query():
    '''Display the query form and then show results if a query is provided
    '''

    searchterms = request.args.get('q','')

    r = db.session.query(func.count(Paper.id))

    papercount = r.first()[0]

    if(searchterms != ''):

        papers = Paper.query.limit(30).all()

        return render_template("query_result.html",
            papers=papers)
    else:
        return render_template("query.html", 
            paper_count=papercount, 
            corescs=C_ABRV)
