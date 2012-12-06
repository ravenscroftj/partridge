from flask.views import View
from flask import render_template

class IndexView(View):
    
    def get_template(self):
        return "index.html"

    def dispatch_request(self):
        return render_template(self.get_template())
