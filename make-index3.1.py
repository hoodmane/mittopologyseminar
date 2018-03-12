#!/usr/bin/python

####
#### Includes and Setup
####

from common import *
from multiprocessing import Pool
import signal

from itertools import groupby # For handling double headers (two talks same day)
import config
os.chdir(config.working_directory)

organizer_email = config.organizer_email
organizer_first_name = config.organizer_first_name
organizer_last_name = config.organizer_last_name
try:
    webmaster_email = config.webmaster_email
except AttributeError:
    webmaster_email = organizer_email
    
local_timezone = time.timezone / 60 / 60 # get the current time zone offset, ignoring daylight saving time (given in seconds, divide by 60 twice to get hours)
epoch = datetime.fromtimestamp(0) # For converting datetime object to time object (time constructor takes seconds since Jan 1st 1970) for finding out about daylight saving time.
standard_time = datetime.strptime(config.standard_time, '%H:%M').time()
config.standard_time = standard_time 
standard_duration = timedelta(hours = int(config.standard_duration.split(":")[0]), minutes=int(config.standard_duration.split(":")[1]))
config.standard_duration = standard_duration


### Templates
jinjaEnv = jinja2.Environment( loader = jinja2.FileSystemLoader('templates') )
jinjaEnv.globals['isfile'] = os.path.isfile
jinjaEnv.globals['config'] = config

indexTemplate = jinjaEnv.get_template('index.html').render
pastSeminarsTemplate = jinjaEnv.get_template('pastseminars.html').render
linksTemplate = jinjaEnv.get_template('links.html').render

talkTemplate = jinjaEnv.get_template('talk.html').render
pastSemesterTemplate = jinjaEnv.get_template('pastsemester.html').render
posterTemplate = latexJinjaEnv.get_template('poster.tex').render

dispatchEmailTemplate = jinjaEnv.get_template('email_dispatch.html').render

textEmailTemplate = jinjaEnv.get_template('email.text').render
htmlEmailTemplate = jinjaEnv.get_template('email.html').render
textDoubleEmailTemplate = jinjaEnv.get_template('email_double_header.text').render
htmlDoubleEmailTemplate = jinjaEnv.get_template('email_double_header.html').render

markdownTemplate = jinjaEnv.get_template('markdown.html').render

markdown = markdown.Markdown(extensions=[myExtension])
markdown.notes_path = 'notes/'
markdown.base_path = ''


dategetter = lambda x: x.date.date()
timegetter = lambda x: x.date


### Handle command line arguments, dump options into "args" dictionary
parser = argparse.ArgumentParser(description = 'Update the Topology Seminar webpage')
parser.add_argument('--make-old-posters', action = 'store_true')
parser.add_argument('--make-old-talks'  , action = 'store_true')
parser.add_argument('--send-email', nargs='?', const='most_recent', default=False)
parser.add_argument('--test-email', nargs='?', const='most_recent', default=False)

# If the user ran it with "python make-index3.1.py" instead of ./make-index3.1.py, the first argument will be make-index3.1.py
if sys.argv[0].find("make-index") != -1:
   sys.argv.pop(0)

args = parser.parse_args( sys.argv )


##### End setup stuff


### Talk stuff

class Talk:
    def __init__(self, jsondict,
        date,  alt_time = None, alt_weekday = None, alt_room = None,
        cancellation_reason = None, change_reason = None, notice = None, email_notice = None, macros = None,
        title = None, abstract = None, email_abstract = None, no_email=False,
        speaker = None,  institution = None, website = None, notes = None
    ):
        self.jsondict = jsondict
        if not (speaker or cancellation_reason):
            self.invalid = True
            return
        try:        
            day = datetime.strptime(date, '%Y/%m/%d')
            if alt_time:
                t = datetime.strptime(alt_time, '%H:%M').time()
            else:
                t = standard_time
        except ValueError:        
            if date != '':
                print 'Error: "%s" is not a valid date' % date
            self.invalid = True
            return
        if alt_room:
            self.room = alt_room
        else:
            self.room = config.standard_room
        self.invalid = False            
        date = datetime.combine(day, t)
        self.date = date
        self.upcoming = date > datetime.today()
        self.weekday = alt_weekday if alt_weekday else config.standard_weekday
        if self.upcoming and date.strftime('%A') != self.weekday:
           raise ValueError('The date %s but it should be a %s. Either fix the date or add \'"alt_weekday" : "%s"\' to the talk in  talks.json' %  
              (date.strftime("%Y/%m/%d is a %A"),self.weekday,date.strftime("%A")) 
           )
        self.year = date.year 
        self.day = self.date.strftime('%b %d')       
         
        self.cancellation_reason = cancellation_reason        
        self.change_reason = change_reason
        self.notice = notice        
        self.email_notice = email_notice if email_notice else notice     
        self.no_email = no_email   
        
        self.macros = macros if macros else ""

        self.title = title
        self.title_poster = title
        self.title_html = convert_quotes(title) if title else None
        self.title_email = delatex(convert_quotes(title)) if title else None
        self.abstract = abstract
        if(notes):
            self.notes = markdown.convert(notes)
            

        self.email_abstract = None
        self.email_abstract_html = None
        self.email_abstract_text = None
        if abstract:
            self.abstract_html = paragraphs_to_html(convert_quotes(abstract))
            if not email_abstract:
                email_abstract = abstract
                
            self.email_abstract_html = paragraphs_to_html(delatex(convert_quotes(email_abstract))) # latex_to_mml( -- , self.macros)
            self.email_abstract_text = paragraphs_to_text(delatex(     convert_quotes(email_abstract)))
        
        self.posterfilename = date.strftime('%Y%m%d') + "-" + (sanitizeFileName(speaker) if speaker else "No Speaker")

        # self.speaker might have a URL; self.speaker_name is just the name
        self.speaker_name = speaker
        if speaker:
           self.speaker = MaybeLink(convert_quotes(speaker), website)
        else:
           self.speaker = None
        self.institution = institution
        self.initInstitutions()
        self.makeGoogleLink()
            

    def initInstitutions(self):
        if not self.institution:
           print "Warning: talk with date %s has no institution for the speaker %s" % (self.date.strftime("%m/%d/%Y"), talk['speaker'])
           self.institutionLink = None
           self.institutionText = None
           return

        institutionList = []
        for inst in self.institution.split(";"):
            try:
                institutionList.append(institutionTable[sanitize_key(inst)])
            except KeyError:
                institutionList.append(MaybeLink(inst, ''))
                print "--- Institution '%s' has no entry in institutionTable.csv. Please add it." % inst.strip()
                
        if len(institutionList) <= 2:
            self.institutionLink = " and ".join(map(str,institutionList))
            self.institutionText = " and ".join(map(lambda inst: inst.text,institutionList))
        else:
            self.institutionLink = ", ".join(map(str,institutionList[:-1])) + ", and " + str(institutionList[-1])
            self.institutionText = ", ".join(map(lambda inst: inst.text,institutionList[:-1])) + ", and " + institutionList[-1].text
        self.institutionLink = convert_quotes(self.institutionLink)

   # creates a link to a Google calendar event
    def makeGoogleLink(self):
      if not (self.speaker):
          return
      l = ['http://www.google.com/calendar/event?action=TEMPLATE&text=', self.speaker.text]
      if self.title:
          l.append(': %s' % self.title)
      dst = time.localtime((self.date-epoch).total_seconds()).tm_isdst
      l.append('&dates=%s%d%s' % ((self.date.strftime('%Y%m%dT'),self.date.hour + local_timezone - dst,self.date.strftime('%M00Z'))))
      end = self.date + standard_duration
      l.append('/%s%d%s' % (end.strftime('%Y%m%dT'), end.hour + local_timezone - dst, end.strftime('%M00Z')))
      l.append('&sprop=MIT Topology Seminar&location=%s' % 'MIT ' + self.room)
      self.googleLink = ''.join(l)
        
                
    def __str__(self):
       return talkTemplate(vars(self))

def init_worker():
    signal.signal(signal.SIGINT, signal.SIG_IGN)

def makeposters(talklist,poolsize=5):
    p = Pool(poolsize,init_worker)
    try:
        result = p.map_async(makeposter,talklist)
        while True:
            if result.ready():
                return result.get()
            time.sleep(1)
    except KeyboardInterrupt:
        print "Quitting!"
        p.terminate()
        p.join()
        sys.exit()

def makeposter(talk):
    # if there is no talk we make no poster!
#    if talk.cancellation_reason:
#        return
    # if there is no title there's no point in making a poster
    if not talk.title:
        return 
    try: 
        latexPoster(talk.posterfilename, posterTemplate(dict(vars(talk), contact_email = organizer_email)))
    except IOError:
        pass
    

class Email:
    # Usually talks is a single talk, but on a rare ocassion there is a double header.
    # TODO: add handling for weird day of week. no_email flag.
    # If there are ever two talks in the same week but on different days, will have to figure out what to do...
    def __init__(self,talks):
        self.talks = talks
        if talks[0].cancellation_reason:
            return
        if not talks[0].speaker:
            return
        for talk in talks:
            if talk.no_email:
                return
    	talk = talks[0]
    	self.date = talk.date
    	
        if not talk.title:
            msg = MIMEText(            
                "Please add a title and hopefully an abstract for " + talk.speaker_name + "'s talk and run '%s --send-email'" % scriptname
            )
            msg['To'] = organizer_email
            msg['From'] = organizer_email
            msg['Subject'] = "No title for " + talk.date.strftime("%A") + "'s talk"
            self.message = msg
            self.list_email = None
            return
        
        msg = MIMEMultipart('alternative')
        msg['From'] = organizer_email
        msg['To'] = config.target_email
        
    	if len(talks) == 1:
            self.subject = "MIT topology seminar: " + talk.speaker_name
            changelist = []
            if talk.date.timetz() != standard_time:
               changelist.append("TIME") 
            if talk.weekday != config.standard_weekday:
               changelist.append("DAY") 
            if talk.room != config.standard_room:
               changelist.append("ROOM")     
            
            if len(changelist)>0:
                self.subject += " (NOTE THE CHANGE OF "
                if 1<=len(changelist)<=2:
                     self.subject += " AND ".join(changelist)
                elif len(changelist)>2:
                    self.subject  += ", ".join(changelist[:-1]) + ", AND " + str(changelist[-1]) 
                self.subject += ")"
            
    	elif len(talks) == 2:
    	    self.subject = "MIT topology seminar: " + \
    			talks[0].speaker_name + talks[0].date.strftime(" (%-I:%M)") + " and " + \
    			talks[1].speaker_name + talks[1].date.strftime(" (%-I:%M)")		
    	else:
    	    error
    	msg['Subject'] = self.subject
            
        email_dict = dict(  
    	    talk   = talk,
    	    talks  = talks,              
                config = config,
                extra_prefix = ''
        )
        
        # TODO: The mixture of the abstract / noabstract and one talk two talks logic here is a little muddled. Straighten it out?    
        # TODO: Finish the setup for alt_time and alt_room for single talks.
        # if there is an abstract, just make an email to the google group
        if talk.abstract:
    	   if len(talks) == 1:
              self.textEmail = re.sub("<.*?>","",textEmailTemplate(email_dict))
              self.htmlEmail = htmlEmailTemplate(email_dict)
           else:
              self.textEmail = textDoubleEmailTemplate(email_dict)
              self.htmlEmail = htmlDoubleEmailTemplate(email_dict)
           msg.attach(MIMEText(self.textEmail,'plain', 'UTF-8'))
           msg.attach(MIMEText(self.htmlEmail,'html', 'UTF-8'))
           self.message = msg
           self.list_message = msg
           self.message_no_abstract = None
        # if not, make a '-noabs' email to the group and the main email to the organizer complaining
        else:
           email_dict['abstract'] = ''
           msg.attach(MIMEText(textEmailTemplate(email_dict), 'plain', 'UTF-8'))
           msg.attach(MIMEText(htmlEmailTemplate(email_dict), 'html', 'UTF-8'))
           self.message_no_abstract = msg
           self.list_message = msg
                   
           msg = MIMEMultipart('alternative')
           msg['From'] = organizer_email
           msg['Reply-to'] = organizer_email
           msg['To'] = organizer_email
           msg['Subject'] = "No abstract for " +talk.date.strftime("%A") + "'s talk"
           email_dict['extra_prefix'] = \
             "Either add an abstract and run '%s --send-email' or run '%s --send-email-no-abs'.\n\n " % (scriptname,scriptname)
           msg.attach(MIMEText(textEmailTemplate(email_dict), 'plain', 'UTF-8'))
           self.message = msg
               
        self.writeToFile()
           
        

    def sendToOrganizer(self):
        self.list_message.replace_header('To', webmaster_email)
        sendEmail(self.list_message)
        print("Sent email to organizer")
        return
    
    def sendToList(self):
        if promptSend(config.target_email):
            self.markSent()
            sendEmail(self.list_message)
            print("Sent email to list")
        return
    
    def send(self):
        if self.message['To'] == config.target_email:
            self.sendToList()
        else:
            sendEmail(self.message)
            print("Sent email to organizer")
        return
    
    def writeToFile(self):
        writeFile('emails/email_' + self.date.strftime("%m-%d") + '.dat', pickle.dumps(self.message))
        if self.message_no_abstract:
            writeFile('emails/email_' + self.date.strftime("%m-%d") + '_noabs.dat', pickle.dumps(self.message_no_abstract))
        return
        
    def markSent(self):
        writeFile('emails/mark_' + self.date.strftime("%m-%d") + '.dat','sent')
        return

def makeemail(talks,temp=[]):
    email = Email(talks)
    if args.test_email:
        if not temp:
            email.sendToOrganizer()
            temp.append(1)
    return email

        







##############################################################################
##############################################################################
##############################################################################
##############################################################################
##############################################################################
##############################################################################

def makepasttalkslist(pastlist):
    pastlist.sort(key=dategetter, reverse=True)
    sem = ''
    past = []
    cursemtalks = ''
    season=''
    for talk in pastlist:
        curseason = getSeason(talk.date)
        cursem = curseason + " " + str(talk.date.year)
        if cursem != sem and sem: # Don't want to do this on first iteration
            past.append( pastSemesterTemplate(dict(
                season = season.lower(),
                semester = sem,
                talks = cursemtalks
            )))
            cursemtalks = ''
        sem = cursem        
        season = curseason
        cursemtalks += str(talk)
    past.append( pastSemesterTemplate(dict( # Catch missing last semester
        season = season.lower(),
        semester = sem,
        talks = cursemtalks
    )))
    past = ''.join(past)
    return past


def makeoldpasttalks():
    talkReader = csv.DictReader(open('oldtalks.csv'))
    talks = []
    for talk in talkReader:
        if talk['REASON'] != '':
            talks.append(Talk(date=talk['DATE'], cancellation_reason=talk['REASON']))
        elif talk['SPEAKER'] != '':
            if talk['INSTITUTION'] != '':
                talks.append(Talk(jsondict=None,date=talk['DATE'], speaker=talk['SPEAKER'],
                                  institution=talk['INSTITUTION'],
                                  website=talk['WEBSITE'], title=talk['TITLE'],
                                  abstract=talk['ABSTRACT'].replace("\\\\","\n\n"), notice=talk['SPECIAL']))
    if args.make_old_posters:
        makeposters(talks,10)
    past = makepasttalkslist(talks)
    past = past.encode('ascii', 'xmlcharrefreplace')
    writeFile('oldpastseminars.html', past)



print "Reading data files"
# insert downloading stuff from Google here <--what the heck does this mean??

instReader = csv.DictReader(open('institutionTable.csv'))
institutionTable = {}
for row in instReader:
    instKeys = row['KEYS'].split(";")
    instName = row["NAME"]
    institutionTable[sanitize_key(instName)] = MaybeLink(instName, row['LINK'])
    for instKey in instKeys:
        instKey = instKey.strip()
        if instKey != '':
            institutionTable[sanitize_key(instKey)] = MaybeLink(instName, row['LINK'])


if args.make_old_talks:
    print "Making old past talks"
    makeoldpasttalks()



# No special handling by semester here, we'll figure out the semester for each talk later using the date
# Note that the semester files are not processed in order, but we don't care because we sort the individual talks by date.
# In make-juvitop.py, the seminar_data files are sorted, we can copy the code from there if at some point we need to sort them here too.
talks = []
for semJSON in glob.glob('seminar_data/*.json'):
    for talk in processJSON(semJSON):
        talks.append(Talk(talk,**talk))
        if talks[-1].invalid:
            talks.pop()


upcoming = [talk for talk in talks if talk.upcoming]
upcoming.sort(key=dategetter)



# Group upcoming talks by date to handle emails for double headers
talkgroups = []
for k, g in groupby(upcoming,dategetter):
   l=sorted(g,key=timegetter)
   for k, g in groupby(l,timegetter):
        if len(list(g))>1:
            print("Warning: you have two talks at the same time. Either this is a copy-paste error, or you forgot to include an 'alt_time' for one (or both) of the talks.")
   talkgroups.append(l)


## Jon emails
## So the idea here is that we want to send an initial email when the talk is two weeks away which has the basic details and a link to the poster.
## After this has been sent, we have to keep him updated on changes so we send him emails with a list of changes every time an update is made
## but we don't want to spam him with tons of emails if the organizer changes a few things in quick succession, so we wait ten minutes before sending an email
## and then send a list of all changes that occurred in the ten minutes from the first one. We want this python program to quick gracefully even while waiting
## for the email to be sent, so seems that the email has to be sent by a second program which is emails/sendEmailToJon.py

def sendEmailToJon(date, subject, body,newJsonDicts):
   dataFileName = date.strftime('emails/dict-%b-%d.dat') 
   emailFileName = date.strftime('emails/sending-%b-%d.dat')
   if(not os.path.isfile(emailFileName)):
      subprocess.Popen(['nohup', 'sendNoticeToJon.py',emailFileName, '>/dev/null', '2>&1'], stdout=open('/dev/null', 'w'), stderr=open('emails/testerr.log', 'w'))
   writeFile(emailFileName, pickle.dumps(dict(subject = subject, body = body,newJsonDicts = newJsonDicts, dataFileName = dataFileName)))      

for g in talkgroups:
   # dataFileName is the name of the file storing the record for the current talk if an email has been sent to Jon yet.
   dataFileName = g[0].date.strftime('emails/dict-%b-%d.dat') 
   newJsonDicts = map(lambda x: x.jsondict,g)
   try:
      oldJsonDicts = pickle.load(file(dataFileName))
   except: # dataFileName doesn't exist, so haven't sent Jon an email yet for this talk, check if it's soon enough that we should send it
      if (g[0].date.date() - datetime.today().date()).days <= 14: # is the talk in the next two weeks?
        sendEmailToJon(g[0].date, "Upcoming talk: " + g[0].day,  dispatchEmailTemplate(dict(talk=g[0])), newJsonDicts)
        
   else: # Have sent Jon an email
      if oldJsonDicts!=newJsonDicts: # check if there's been an update we need to tell him about
         print "changed"
         changedFields=[]
         changes="Changes: \n"
         for k, v in newJsonDicts[0].iteritems():
            if(k not in oldJsonDicts[0] or v!=oldJsonDicts[0][k]):
               changes+= str(k) +  ": " + str(v) + '\n'
         changes += "\n\n" + "And the poster link: http://math.mit.edu/topology/posters/" + g[0].posterfilename + ".pdf"
         sendEmailToJon(g[0].date, "Changes for " + g[0].day + " talk", changes, newJsonDicts)

            

print 'Generating posters'
makeposters(upcoming)

print 'Generating emails'
os.system("rm emails/email*")
emails = map(makeemail, talkgroups)
if args.send_email:
    emails[0].sendToList()
   



print 'Generating upcoming talks page'
if upcoming:
    upcoming = map(str, upcoming)
    # we want to expand the next two talks
    upcoming = ''.join(upcoming[:2]).replace('"checkbox"', '"checkbox" checked') + ''.join(upcoming[2:])
    # Set up unicode for html
    upcoming = upcoming.encode('ascii', 'xmlcharrefreplace')
else:
    upcoming = "<b> There are no more talks this semester. Check back next semester.</b><br/><br/><br/>"

writeFile('index.html', 
    indexTemplate(
        dict(
            upcoming = upcoming, 
            standard_weekday = config.standard_weekday, 
            standard_time = str((standard_time.hour - 1) % 12 + 1) + ":" +  str(standard_time.minute),
            standard_room = config.standard_room,
            webmaster_email = webmaster_email
        )
    )
)


print 'Generating past talks page'

# for past talks we split them into semesters
pasttalks = [talk for talk in talks if not talk.upcoming]
if args.make_old_posters:
    makeposters(pasttalks)

past = makepasttalkslist(pasttalks)

# and we want to expand the first semester
past = past.replace('"checkbox"', '"checkbox" checked', 1)

# Set up unicode for html
past = past.encode('ascii', 'xmlcharrefreplace')

pastold = readFile('oldpastseminars.html')

writeFile('pastseminars.html', 
    pastSeminarsTemplate(
        dict(
            past = past, 
            pastold = pastold,
            webmaster_email = webmaster_email
        )
    )
)



print 'Generating links page'
writeFile('links.html', 
    linksTemplate(
        dict(
            organizer_name = organizer_first_name + " " + organizer_last_name,
            organizer_email = organizer_email,
            webmaster_email = webmaster_email
        )
    )
)

writeFile('README.html',markdownTemplate(dict(content = readmeMarkdown(readFile('README.md').encode('ascii', 'xmlcharrefreplace')))))
