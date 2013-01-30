""" Library of Werkzeug URL converters for papers etc """

from werkzeug.routing import BaseConverter

from partridge.models import db
from partridge.models.doc import Paper


class PaperConverter(BaseConverter):

    regex = '([0-9]+)'

    def to_python(self, id):
        '''Given an ID, query the database and return paper'''

        return Paper.query.filter_by(id=id).first()


    def to_url(self, paper):
        '''Given paper object, return ID as string'''
        return str(paper.id)
