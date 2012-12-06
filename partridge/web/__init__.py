'''
Partridge's main web interface entrypoint

'''

from flask import Flask, render_template
from partridge.models import db


def create_app( config ):
    """Register app object and return to caller"""
    app = Flask(__name__)
    app.config.update(config)
    db.init_app(app)
    return app
