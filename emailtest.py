#!/usr/bin/python
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import pickle
import sys

#msg = pickle.load(file('emails/email_' + filedatename))
#msg.replace_header('To',"hood@mit.edu")

msg = MIMEMultipart('alternative')
msg['From'] = "a@math.mit.edu"
msg['Reply-To'] = "a@math.mit.edu"
msg['Reply-To'] = "b@math.mit.edu"
msg['To'] = "hood@mit.edu"
msg['Subject'] = "No abstract"
msg.attach(MIMEText("Hello", 'plain', 'UTF-8'))


smtp = smtplib.SMTP("outgoing.mit.edu")
smtp.sendmail(msg['From'], msg['To'], msg.as_string())
