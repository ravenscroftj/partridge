"""Upload form views for adding papers to the database"""

import os
import uuid
from flask import render_template, request, current_app
from werkzeug import secure_filename

from partridge.views import frontend

from partridge.models import db
from partridge.models.doc import PaperWatcher

ALLOWED_EXTENSIONS = ['.xml','.pdf']


@frontend.route("/upload", methods=['GET','POST'])
def upload():
    """Display the upload form allowing users to add their papers
    """

    if(request.method == "POST"):


        destdir = current_app.config['PAPER_UPLOAD_DIR']

        for f in request.files:

            file = request.files[f]

            name,ext = os.path.splitext(file.filename)

            if ext in ALLOWED_EXTENSIONS:

                fname = str(uuid.uuid4()) + ext

                if ("email" in request.args) & (request.args['email'] != ""):
                    
                    current_app.logger.info("Registering watcher for paper at email %s",
                    request.args['email'])

                    watcher = PaperWatcher()
                    watcher.email = request.args['email']
                    watcher.filename = fname

                    db.session.add(watcher)
                    db.session.commit()
                
                #now save the file
                file.save(os.path.join(destdir,fname))




    return render_template("upload.html")
