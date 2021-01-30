from flask import jsonify, Blueprint, request

from partridge.util.querybuilder import PaperQueryBuilder
from partridge.models.doc import Paper,Sentence,Author, C_ABRV, PAPER_TYPES
from sqlalchemy import func, or_, and_


api_bp = Blueprint("api", __name__, url_prefix="/api")


UPPER_LIMIT = 50

@api_bp.route("/papers/")
@api_bp.route("/papers/<int:limit>/")
@api_bp.route("/papers/<int:limit>/<int:offset>/")
@api_bp.route("/papers/type/<string:type>/")
@api_bp.route("/papers/type/<string:type>/<int:limit>/")
@api_bp.route("/papers/type/<string:type>/<int:limit>/<int:offset>/")
def list_papers(type="", offset=0, limit=UPPER_LIMIT):

    #do paper counts for all paper types
    paper_types = {x:Paper.query.filter(Paper.type == x).count() for x in PAPER_TYPES}

    qb = PaperQueryBuilder()

    constraints = { x:request.args.get(x,'') for x in request.args}
    
    if type != "":
        constraints['papertype'] = type

    qb.build_query(**constraints)

    paper_q = qb.get_query()

    for key in request.args:
        value = request.args.get(key,'')
        attr = key.split("_")[0]

    papers = paper_q.limit(min(limit, UPPER_LIMIT)).offset(offset).all()

    return jsonify({
        "total_paper_count"  : paper_q.count(),
        "current_page_count" : len(papers),
        "papers" : [p.json() for p in papers]
        })
