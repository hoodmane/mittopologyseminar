#!/usr/bin/python
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import pickle
import sys

msg = MIMEMultipart('alternative')
msg['From'] = "topology-seminar-event-dispatch@math.mit.edu"
msg['Reply-To'] = "hood@mit.edu"
msg['To'] = "hood@mit.edu"
msg['Subject'] = "test"

msg.attach(MIMEText("Hello there!",'plain', 'UTF-8'))

#filedatename = sys.argv[1]

#msg = pickle.load(file('emails/email_' + filedatename))
#msg.replace_header('To',"hood@mit.edu")
smtp = smtplib.SMTP("outgoing.mit.edu")
smtp.sendmail(msg['From'], msg['To'], msg.as_string())
