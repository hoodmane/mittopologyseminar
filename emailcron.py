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
os.umask(0002)

def markSent(filedatename):
   fd = os.open('emails/mark_' + filedatename, os.O_WRONLY | os.O_CREAT)
   os.write(fd, 'sent')
   os.close(fd)   

def isMarked(filedatename):
   print('mark_' + filedatename)
   print(subprocess.call('ls emails/mark_' + filedatename + '> /dev/null 2>&1' ,shell=True))
   return  0==subprocess.call('ls emails/mark_' + filedatename + '> /dev/null 2>&1' ,shell=True)

email_mark_files = subprocess.check_output('ls emails', shell=True).split('\n')[:-1]


emailfiles = [(x[:-4].split("_")) for x in email_mark_files]
emailfiles= [(l[0],datetime.strptime(l[1] + "-" + str(datetime.today().year),'%m-%d-%Y'),"_".join(l)+".dat") for l in emailfiles]

markfiles = [(f[1],f[2]) for f in emailfiles if f[0]=="mark"]

for f in markfiles:
   if f[0].date()<datetime.today().date():
       os.system("rm emails/"+f[1])


markfiles = [f[1][5:] for f in markfiles if f[0].date()>=datetime.today().date()]

emails_to_send = [f[1] for f in emailfiles if f[0]=="email" and (f[1].date() - datetime.today().date()).days <= 2]

if len(emails_to_send) == 0:
    sys.exit()
    
filedatename = emails_to_send[0].strftime('%m-%d.dat')



test = False

# You MUST use msg.replace_header if you want to prevent it from sending to topology.googlegroups. 
# DONT USE msg['To']= blah, that just adds another recipient.

# Test if the email has been marked as sent, in which case don't send it.
if filedatename not in markfiles and not test:
   msg = pickle.load(file('emails/email_' + filedatename))
   #msg.replace_header('To',"hood@mit.edu")
   smtp = smtplib.SMTP("outgoing.mit.edu")
   smtp.sendmail(msg['From'], msg['To'], msg.as_string())
   markSent(filedatename)

if test:
   msg = pickle.load(file('emails/email_' + filedatename))
   msg.replace_header('To',"hood@mit.edu")
   smtp = smtplib.SMTP("outgoing.mit.edu")
   print(msg)
   smtp.sendmail(msg['From'], msg['To'], msg.as_string())

