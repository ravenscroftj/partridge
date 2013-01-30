"""Upload form views for adding papers to the database"""

import os
import uuid
from flask import render_template, request, current_app
from werkzeug import secure_filename


ALLOWED_EXTENSIONS = ['.xml','.pdf']

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
                file.save(os.path.join(destdir,fname))



    return render_template("upload.html")
