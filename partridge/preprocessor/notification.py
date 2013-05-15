import smtplib
import traceback
import os

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from partridge.config import config

from flask import url_for

from partridge.models import db
from partridge.models.doc import PaperFile, PaperWatcher

app = db.app

#---------------------------------------------------------------

def inform_watcher(logger, papername, **kwargs):
    """Informa watchers of papers and what happened to them"""
    
    basename = os.path.basename(papername)

    q = PaperWatcher.query.filter(PaperWatcher.filename == basename)

    if(q.count() > 0):
        w = q.first()

        logger.info("Informing %s about paper %s", w.email, w.filename) 

        if "paperObj" in kwargs:
            
            if "exists" in kwargs:
                send_exists_email( papername, kwargs['paperObj'], w.email)

            else:
                send_success_report( kwargs['paperObj'], w.email)
        else:

            e = kwargs['exception']
            send_error_report( e, e.traceback,
                [papername], w.email)

        db.session.delete(w)
        db.session.commit()

#---------------------------------------------------------------
def send_exists_email(filename, paperObj, to):
    """If a paper exists in the system, send the uploader an email"""

    file = os.path.basename(filename)

    ctx=app.test_request_context()
    ctx.push()
    url = url_for(".paper_profile", the_paper=paperObj, _external=True)
    ctx.pop()
 
    txt = """Hi There,

Thanks for submitting your paper to Partridge. We've done some analysis and
determined that we already have a paper with the same DOI or an identical title
and set of authors in our database.

Paper Title: %s
DOI (If Available): %s

You can view the paper at the following URL:
%s

Your uploaded paper file will be purged from the queue to prevent duplication.
If you think this is an error, forward this email to queries@papro.org.uk and
we will investigate.

Thanks,

The Partridge Paper Processing Robot """ % (paperObj.title, paperObj.doi, url)

    msg = MIMEText(txt)
    msg['Subject'] = "Partridge: Paper Already Exists!"
    msg['From']  = config['NOTIFICATION_FROM']
    msg['To'] = to

    send_mail( msg, to )


#---------------------------------------------------------------

def send_error_report( error, tb, paper_files, to=config['NOTIFICATION_ADDRESS']):
    """ Send an email report when a paper fails to process
    """

    if not config.has_key('NOTIFICATION_ADDRESS'): return

    msg = MIMEMultipart()
    msg['Subject'] = "Partridge Failed to process a paper"
    msg['From']  = config['NOTIFICATION_FROM']
    msg['To'] = to
    msg.preamble = "Message from the partridge paper processing daemon"

    #encode the message
    text = """Hi There,

Thanks for submitting your paper to Partridge for processing. Unfortunately,
there was an error handling your paper and it couldn't be added to the
database. The error message is below as well as the paper files that you
uploaded/requested.

Thanks,

The Partridge Paper Processing Monkey
    
Failed to process a paper because %s \n""" % error

    for line in tb:
        text += line

    txtmsg = MIMEText(text)
    msg.attach(txtmsg)

    for file in paper_files:
        with open(file, 'rb') as f:
            attachment = MIMEText(f.read(), _subtype="xml")
        
        basename = os.path.basename(file)

        attachment.add_header('Content-Disposition',
            'attachment',filename=basename)

        msg.attach(attachment)

    send_mail( msg, to)

#-----------------------------------------------------------------------------

def send_success_report( paperObj, to=config['NOTIFICATION_ADDRESS']):
   
    ctx=app.test_request_context()
    ctx.push()
    url = url_for(".paper_profile", the_paper=paperObj, _external=True)
    ctx.pop()
 
    txt = """Hi There,

Thanks for submitting your paper to Partridge. We've done some analysis and
your paper has been included into our corpus.

Paper Title: %s
Paper Type: %s

You can view the paper at the following URL:
%s

Thanks,

The Partridge Paper Processing Monkey """ % (paperObj.title, paperObj.type, url)

    msg = MIMEText(txt)
    msg['Subject'] = "Partridge Paper Success Notification"
    msg['From']  = config['NOTIFICATION_FROM']
    msg['To'] = to

    send_mail( msg, to )
#-----------------------------------------------------------------------------

def send_mail( msg, to ):
    s = smtplib.SMTP(config['NOTIFICATION_SMTP_SERVER'])
    s.login(config['NOTIFICATION_SMTP_USER'], 
        config['NOTIFICATION_SMTP_PASWD'])
    s.sendmail(config['NOTIFICATION_FROM'], to ,msg.as_string())
    s.quit()

