"""Views related to querying partridge"""

from flask import render_template,request,jsonify

from partridge.views import frontend

from partridge.models import db
from partridge.models.doc import Paper,Sentence,Author, C_ABRV, PAPER_TYPES

from sqlalchemy import func, or_, and_

PAGE_LIMIT = 10

@frontend.route("/query")
def query():
    '''Display the query form and then show results if a query is provided
    '''

    searchterms = request.args.get('q','')

    papercount = Paper.query.count()

    #do paper counts for all paper types
    paper_types = {x:Paper.query.filter(Paper.type == x).count() for x in PAPER_TYPES}


    if(searchterms != ''):

        paper_q = Paper.query
        author_q = Author.query

        clauses = []
        offset = 0

        constraints = { x:request.args.get(x,'') for x in request.args}

        from partridge.util.querybuilder import PaperQueryBuilder

        pq = PaperQueryBuilder()
        pq.build_query(**constraints)

        paper_q = pq.get_query()

        papers = paper_q.limit(PAGE_LIMIT).offset(offset).all()

        result_count = len(papers)

        return jsonify(html=render_template("query_result.html",
            papers=papers), total=paper_q.count(), count=len(papers))
    else:
        return render_template("query.html", 
            paper_count=papercount,
            limit=PAGE_LIMIT,
            corescs=C_ABRV,
            paper_types=paper_types)
