#!/usr/bin/python

####
#### Includes and Setup
####
import os.path
import sys
from common import *

emailFileName = "emails/" + sys.argv[1]

# Wait ten minutes
time.sleep(600)

emailData = pickle.load(file(emailFileName))
os.remove(emailFileName)
subject = emailData.subject
body = emailData.body
newJsonDicts = emailData.newJsonDicts
dataFileName = emailData.dataFileName
    
msg = MIMEMultipart('alternative')
msg['From'] = "topology-seminar-event-dispatch@math.mit.edu"
msg['Reply-To'] = "hood@mit.edu"
msg['To'] = "harmonjo@mit.edu"
msg['cc'] = "hood@mit.edu"
msg['Subject'] = subject
msg.attach(MIMEText(body,'plain', 'UTF-8'))
smtp.sendmail(msg['From'], [msg['To'], msg['cc']], msg.as_string())
writeFile(dataFileName,pickle.dumps(newJsonDicts))


