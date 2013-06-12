"""A set of tools for building complex queries for papers"""

from sqlalchemy import func, or_, and_
from partridge.models.doc import Paper,Sentence,Author, C_ABRV, PAPER_TYPES
from partridge.models import db

class PaperQueryBuilder:
   
    paper_q = None
    clauses = []
    offset  = 0

    def build_query(self, **constraints):
        
        self.paper_q = Paper.query
        self.clauses = []

        for key in constraints:
            value = constraints[key]
            attr = key.split("_")[0]

            if(attr == "any"):
                self.clauses.append( Paper.id.in_(
                        db.session.query(Sentence.paper_id).filter(Sentence.text.like("%%%s%%" % value) ).subquery()
                ))
   
            elif(attr == "offset"):
                offset = value
   
            elif(attr == "papertype"):
                if value != "":
                    self.clauses.append( Paper.type == value )
   
            elif(attr == "author"):
                self.paper_q = self.paper_q.join("authors")
                self.clauses.append( Author.surname.like("%%%s%%" % value))
   
            elif attr in C_ABRV.keys():
                self.clauses.append(Paper.id.in_(
                        db.session.query(Sentence.paper_id).filter(
                                (Sentence.text.like("%%%s%%" % value)) &
                                (Sentence.coresc == attr)).subquery()
                )) 

    def get_query(self):
        return self.paper_q.filter(and_(*self.clauses))
