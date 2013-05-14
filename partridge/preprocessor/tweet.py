"""
Twitter bot support for partridge preprocessor daemon

"""

from partridge.config import config

from twitter import Twitter, OAuth

from flask import url_for

from partridge.models import db
from partridge.models.doc import PaperFile, PaperWatcher

app = db.app


# see "Authentication" section below for tokens and keys
t = Twitter(
            auth=OAuth(config['TWITTER_OAUTH_TOKEN'], config['TWITTER_OAUTH_SECRET'],
                       config['TWITTER_CONSUMER_KEY'], config['TWITTER_CONSUMER_SECRET'])
           )

url_len = t.help.configuration()['short_url_length']

def tweet_paper( paperObj ):

    available = 117 - url_len

    ctx=app.test_request_context()
    ctx.push()
    url = url_for(".paper_profile", the_paper=paperObj, _external=True)
    ctx.pop()

    if( len(paperObj.title) > available+3):
        title = paperObj.title[:available] + "..."
    else:
        title = paperObj.title

    tweet = "Added paper \"%s\" %s" % (title, url)

    # Update your status
    t.statuses.update(status=tweet)
