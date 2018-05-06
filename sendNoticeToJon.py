#!/usr/bin/python

####
#### Includes and Setup
####
import os.path
import sys
from common import *

emailFileName = sys.argv[1]

# Wait ten minutes
time.sleep(600)

# Have to reoopen the smtp connection because it may die while we are sleeping.
smtp = smtplib.SMTP("outgoing.mit.edu")

emailData = pickle.load(file(emailFileName))
os.remove(emailFileName)
subject = emailData['subject']
body = emailData['body']
newJsonDicts = emailData['newJsonDicts']
dataFileName = emailData['dataFileName']
    
msg = MIMEMultipart('alternative')
msg['From'] = "topology-seminar-events@math.mit.edu"
msg['Reply-To'] = "hood@mit.edu"
msg['To'] = "harmonjo@mit.edu" #"hood@mit.edu"#
msg['cc'] = "hood@mit.edu" 
msg['Subject'] = subject
msg.attach(MIMEText(body,'plain', 'UTF-8'))
smtp.sendmail(msg['From'], [msg['To'], msg['cc']], msg.as_string())
writeFile(dataFileName,pickle.dumps(newJsonDicts))


