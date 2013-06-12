"""
Provide statistics about the currrent state of the preprocesor
"""

from flask import render_template,request,jsonify

from partridge.views import frontend

from partridge.config import config

import xmlrpclib

@frontend.route("/queue")
def show():
    """Show the queue stats"""

    server = config['PP_LISTEN_ADDRESS']
    port   = config['PP_LISTEN_PORT']
    pw     = config['PP_AUTH_KEY']

    uri = "http://%s:%d/" % (server,int(port))

    qm = xmlrpclib.ServerProxy(uri)

    return render_template("queue.html",
        qsize=qm.qsize(),
        average=round(float(qm.average()) / 60.0, 2),
        poolsize=qm.poolsize()
        )
