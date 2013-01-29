"""Upload form views for adding papers to the database"""

def upload():
    """Display the upload form allowing users to add their papers
    """

    return render_template("upload.html")
