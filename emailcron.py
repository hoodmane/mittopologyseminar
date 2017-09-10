#!/bin/python

import sys
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import pickle


from datetime import datetime

import os
import subprocess
import config

os.chdir(config.working_directory)
# This makes sure all files are written with correct permissions?
os.umask(0002)

def markSent(filedatename):
   fd = os.open('emails/mark_' + filedatename, os.O_WRONLY | os.O_CREAT)
   os.write(fd, 'sent')
   os.close(fd)   

# This gets all files in the emails directory that have an underscore.
# They should all be of the form email_date.dat or mark_date.dat
# email_date.dat has a pickled email record, mark_date.dat just indicates that the email for that date has already been sent and shouldn't be duplicated.
emailfiles = subprocess.check_output('ls emails/*_*', shell=True).split('\n')[:-1]

emailfiles = [(x[7:-4].split("_")) for x in emailfiles]
emailfiles = [(l[0],datetime.strptime(l[1] + "-" + str(datetime.today().year),'%m-%d-%Y'),"_".join(l)+".dat") for l in emailfiles]
# At this point, emailfiles is a list of triples: ("mark" or "email", a date object, the original file name)

# Get the marks, now as a pair (date, filename)
markfiles = [(f[1],f[2]) for f in emailfiles if f[0]=="mark"]

# Let's delete any old marks to avoid cluttering our folder
for f in markfiles:
   if f[0].date()<datetime.today().date():
       os.system("rm emails/"+f[1])


# Now send an email for a talk within the next two days that is unmarked
markdates = [ m[0] for m in markfiles]
emails_to_send = [f[2] for f in emailfiles if f[0]=="email" and (f[1].date() - datetime.today().date()).days <= 2 and (f[1] not in markdates)]

# If there are no emails to send, exit
if len(emails_to_send) == 0:
    sys.exit()
    
# We'll only send one email per run
filedatename = emails_to_send[0]


test = False

# You MUST use msg.replace_header if you want to prevent it from sending to topology.googlegroups. 
# DONT USE msg['To']= blah, that just adds another recipient.

if not test:
   # Send email
   msg = pickle.load(file('emails/' + filedatename))
   #msg.replace_header('To',"hood@mit.edu") # Uncomment this to prevent email from being sent to list
   smtp = smtplib.SMTP("outgoing.mit.edu")
   smtp.sendmail(msg['From'], msg['To'], msg.as_string())
   markSent(filedatename.split("_")[1]) # make a mark file to prevent email from being sent again

if test:
   msg = pickle.load(file('emails/email_' + filedatename))
   msg.replace_header('To',"hood@mit.edu")
   smtp = smtplib.SMTP("outgoing.mit.edu")
   print(msg)
   smtp.sendmail(msg['From'], msg['To'], msg.as_string())

