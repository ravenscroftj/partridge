"""Upload form views for adding papers to the database"""

import os
import io
import uuid
import tempfile
from datetime import datetime
from flask import render_template, request, current_app
from werkzeug.utils import secure_filename

from partridge.views import frontend

from partridge.models import db
from partridge.models.doc import PaperWatcher
from partridge.preprocessor import get_minio_client

ALLOWED_EXTENSIONS = ['.xml', '.pdf']


@frontend.route("/upload", methods=['GET', 'POST'])
def upload():
    """Display the upload form allowing users to add their papers
    """

    from partridge.preprocessor.service import annotate_paper

    if(request.method == "POST"):

        now = datetime.now()
        destdir = os.path.join(os.environ.get("PARTRIDGE_UPLOAD_PREFIX", "uploads"), now.strftime("%Y/%m/%d"))

        mc = get_minio_client()

        for f in request.files:

            file = request.files[f]

            name, ext = os.path.splitext(file.filename)

            if ext in ALLOWED_EXTENSIONS:

                fname = str(uuid.uuid4()) + ext

                if ("email" in request.args) & (request.args['email'] != ""):

                    current_app.logger.info(
                        "Registering watcher for paper at email %s", request.args['email'])

                    watcher = PaperWatcher()
                    watcher.email = request.args['email']
                    watcher.filename = fname

                    db.session.add(watcher)
                    db.session.commit()

                # now save the file
                outname = os.path.join(destdir, fname)
                
                with tempfile.TemporaryFile('wb+') as f:
                    file.save(f)
                    flen = f.tell()

                    f.seek(0)

                    mc.put_object(os.getenv("MINIO_BUCKET"), outname,
                              f, flen, file.content_type)

                # enqueue the file to be processed
                annotate_paper.send(os.path.join(destdir, fname))

    return render_template("upload.html")
