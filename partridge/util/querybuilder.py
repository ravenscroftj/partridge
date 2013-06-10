"""A set of tools for building complex queries for papers"""

from sqlalchemy import func, or_, and_
from partridge.models.doc import Paper,Sentence,Author, C_ABRV, PAPER_TYPES

class PaperQueryBuilder:

    paper_q = None
    clauses = []
    offset  = 0

    def build_query(self, *args, **constraints):
        
        self.paper_q = Paper.query

        for key in constraints:
            value = constraints[key]
            attr = key.split("_")[0]

            if(attr == "any"):
                self.paper_q = self.paper_q.join("sentences")
                self.clauses.append( Sentence.text.like("%%%s%%" % value) )

            if(attr == "offset"):
                offset = value

            if(attr == "papertype"):
                if value != "":
                    self.clauses.append( Paper.type == value )

            if(attr == "author"):
                self.paper_q = self.paper_q.join("authors")
                self.clauses.append( Author.surname.like("%%%s%%" % value) | 
                    Author.forenames.like("%%%s%%") % value)

            if attr in C_ABRV.keys():
                self.paper_q = self.paper_q.join("sentences")
                self.clauses.append( ( Sentence.coresc == attr ) & 
                    Sentence.text.like("%%%s%%" % value))

    def get_query(self):
        return self.paper_q.filter(and_(*self.clauses))
