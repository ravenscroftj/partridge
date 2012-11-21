'''
Partridge's main web interface entrypoint

'''

from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
  '''Index view shows the front page for partridge
  '''
  return render_template("index.html")


def serve(port=5000, debug=False):
  app.debug = True
  app.run(port=port)
