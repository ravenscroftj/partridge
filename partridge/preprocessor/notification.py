import smtplib
import traceback

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from partridge.config import config

from flask import url_for

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
    text = "Failed to process a paper because %s \n" % error

    for line in traceback.format_tb(tb):
        text += line

    txtmsg = MIMEText(text)
    msg.attach(txtmsg)

    for file in paper_files:
        with open(file, 'rb') as f:
            attachment = MIMEText(f.read(), _subtype="xml")

        attachment.add_header('Content-Disposition', 'attachment',filename=file)
        msg.attach(attachment)

    send_mail( msg )

#-----------------------------------------------------------------------------

def send_success_report( paperObj, to=config['NOTIFICATION_ADDRESS']):
   
    url = url_for(".paper_profile", paper=paperObj, _external=True)

    txt = """Hi There,

Thanks for submitting your paper to Partridge. We've done some analysis and
your paper has been included into our corpus.

Paper Title: %s
Paper Type: %s

You can see it here %s

Thanks,

The Partridge Paper Processing Monkey """ % (paperObj.title, paperObj.type, url)

    msg = MIMEText(txt)
    msg['Subject'] = "Partridge Paper Success Notification"
    msg['From']  = config['NOTIFICATION_FROM']
    msg['To'] = to

    send_mail( msg )
#-----------------------------------------------------------------------------

def send_mail( msg ):
    s = smtplib.SMTP(config['NOTIFICATION_SMTP_SERVER'])
    s.login(config['NOTIFICATION_SMTP_USER'], 
        config['NOTIFICATION_SMTP_PASWD'])
    s.sendmail(config['NOTIFICATION_FROM'], config['NOTIFICATION_ADDRESS'],msg.as_string())
    s.quit()

