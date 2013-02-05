"""Views related to querying partridge"""

from flask import render_template,request,jsonify
from partridge.models import db
from partridge.models.doc import Paper,Sentence,Author, C_ABRV

from sqlalchemy import func, or_

PAGE_LIMIT = 10

def query():
    '''Display the query form and then show results if a query is provided
    '''

    searchterms = request.args.get('q','')

    r = db.session.query(func.count(Paper.id))

    papercount = r.first()[0]

    if(searchterms != ''):

        paper_q = Paper.query
        author_q = Author.query

        clauses = []
        offset = 0

        #process arguments
        for key in request.args: 
            value = request.args.get(key,'')
            attr = key.split("_")[0]

            if(attr == "any"):
                paper_q = paper_q.join("sentences")
                clauses.append( Sentence.text.like("%%%s%%" % value) )

            if(attr == "offset"):
                offset = value

            if(attr == "author"):
                paper_q = paper_q.join("authors")
                clauses.append( Author.surname.like("%%%s%%" % value) | 
                    Author.forenames.like("%%%s%%") % value)

            if attr in C_ABRV.keys():
                paper_q = paper_q.join("sentences")
                clauses.append( ( Sentence.coresc == attr ) & 
                    Sentence.text.like("%%%s%%" % value))
        
        paper_q = paper_q.filter(or_(*clauses))

        papers = paper_q.limit(PAGE_LIMIT).offset(offset).all()
        
        result_count = len(papers)

        return jsonify(html=render_template("query_result.html",
            papers=papers), total=paper_q.count(), count=len(papers))
    else:
        return render_template("query.html", 
            paper_count=papercount,
            limit=PAGE_LIMIT,
            corescs=C_ABRV)
