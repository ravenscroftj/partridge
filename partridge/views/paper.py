"""View stats and info for a known paper in the database"""
import mimetypes
import os
from flask import render_template, current_app, Response


from partridge.views import frontend
from partridge.preprocessor import get_minio_client

@frontend.route("/paper/<paper:the_paper>")
def paper_profile(the_paper):
    """Given a paper object, render a profile page""" 
    
    return render_template("paperprofile.html", paper=the_paper)

@frontend.route("/file/<file:the_file>")
def paper_file( the_file ):
    r  = Response()
    mc = get_minio_client()
    r.mimetype=mimetypes.guess_type(the_file.path)[0]
    
    try:
        f = mc.get_object(os.getenv('MINIO_BUCKET'), the_file.path)
        r.data = f.read()
    except Exception as e:
        print(e)
    finally:
        f.close()
        f.release_conn()
    return r
