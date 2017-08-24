#!/usr/bin/python

import sys
import os
from datetime import datetime, date, timedelta
import time

import re
import csv
import json
import unicodedata
from string import Template

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

#organizer_email = os.environ['USER'] + "@mit.edu"

import config 

standard_time = datetime.strptime(config.standard_time, '%H:%M').time()
standard_duration = timedelta(hours = int(config.standard_duration.split(":")[0]), minutes=int(config.standard_duration.split(":")[1]))
local_timezone = time.timezone / 60 / 60 # get the current time zone offset, ignoring daylight saving time (given in seconds, divide by 60 twice to get hours)
epoch = datetime.fromtimestamp(0) # For converting datetime object to time object (time constructor takes seconds since Jan 1st 1970) for finding out about daylight saving time.

if (sys.version_info[0],sys.version_info[1]) < (2,5):
    raise "This requires python version 2.5 or greater"
reload(sys)
sys.setdefaultencoding("utf-8")

os.chdir(config.working_directory)

def nonEmpty(x):
    if x == '':
        return None
    else:
        return x
        
# convert string to lowercase and remove accents
def sanitize_key(input_str):
    input_str = re.sub(r"\\.","",input_str).strip().lower().replace("the ","")
    # remove accents from unicode characters
    nkfd_form = unicodedata.normalize('NFKD', unicode(input_str.lower()))
    return u"".join([c for c in nkfd_form if not unicodedata.combining(c)])

def delatex(str):
   # re.sub("\\.bb","\1")
    return delatexquotes(str).replace("\\","").replace("$","")

def delatexquotes(str):
    return str.replace('``','"').replace("`","'").replace("''",'"')


postertemp = Template(file('poster.template').read())

def makeposter(talk):
    # if there is no talk we make no poster!
    if talk.reason:
        return
    # if there is no title there's no point in making a poster
    if not talk.title:
        return

    d = dict(speaker='', abstract='', institution='', title='', contact_email = config.organizer_email, room = config.standard_room)
    d['date'] = '{dt:%A}, {dt:%B} {dt.day}'.format(dt=talk.date)
    hour = talk.date.hour
    minute = talk.date.strftime(':%M')
    if talk.date.hour > 12:
        hour = talk.date.hour - 12
    if talk.date.minute == 0:
        minute = ''
    d['time'] = '%d%s\\,%s' % (hour, minute, talk.date.strftime('%p').lower())
    if talk.speaker:
        d['speaker'] = talk.speaker.text
    if talk.title:
        d['title'] = talk.title
        d['prep'] = 'on'
    else:
        d['title'] = '\\normalsize the topology seminar'
        d['prep'] = 'in'
    if talk.institutions:
        institutions = talk.institutions
        if len(institutions) == 1:
            institution = institutions[0].text
        elif len(institutions) == 2:
            institution = institutions[0].text + " and " + institutions[1].text
        else:
            last = institutions.pop()
            institution = ""
            for inst in institutions:
                insitution = institution + inst.text + ", "
            insitution = institution + "and " + last.text
        d['institution'] = institution
    if talk.abstract:
        d['abstract'] = re.sub("<.*?>","",talk.abstract)

    raw = postertemp.substitute(d)
    try:
        file('posters/%s.tex' % talk.name, 'w').write(raw)
    except IOError:
        pass
    os.system('pdflatex -interaction=batchmode "posters/%s.tex" >/dev/null' % talk.name)
    os.system('mv "%s.pdf" posters/ && rm -f "%s."*' % (talk.name, talk.name))
    os.system('chmod 755 "posters/%s.pdf"' % (talk.name))

email_text_template = Template(file('email_text.template').read())
email_html_template = Template(file('email_html.template').read())

def makeemail(talk):
    # If there's no talk, don't make an email (maybe make an email clarifying that the talk has been cancelled?)
    if talk.reason:
        return
    # If there's no title, make an email to organizer complaining
    
    if not talk.title:
        msg = MIMEText(            
            "Please add a title and hopefully an abstract for " + talk.speaker_name + "'s talk, run make-index{version}.py and " \
            "then execute 'sendmail -t emails/email_" + talk.date.strftime("%m-%d") + ".txt'" \
            "or 'sendmail -t 'emails/email-noabs_" + talk.date.strftime("%m-%d")+".txt'"
        )
        msg['To'] = config.organizer_email
        msg['From'] = config.organizer_email
        msg['Subject'] = "No title for " + talk.date.strftime("%A") + "'s talk"
        file = open('emails/email_' + talk.date.strftime("%m-%d") + '.txt', 'w')
        file.write(str(msg))
        file.close()
        return
        
    msg = MIMEMultipart('alternative')
    msg['From'] = config.organizer_email
    msg['To'] = config.target_email
    msg['Subject'] = "MIT topology seminar: " + talk.speaker_name
    
    email_dict = dict(                
        organizer_name = config.organizer_first_name,
        title = delatex(talk.title),
        speaker = talk.speaker_name, 
        day = talk.date.strftime("%A"),
        date = '{dt:%B} {dt.day}'.format(dt = talk.date),
        time = str((standard_time.hour - 1) % 12 + 1) + ":" +  str(standard_time.minute),
        room = config.standard_room,
        extra_prefix = ''
    )
    
    if talk.email_abstract:  # if there is an abstract, just make an email to the google group
        email_dict['abstract'] = "\n\n\nAbstract:\n\n" + delatex(re.sub('\n\s*\n','aogheaohtaope', talk.email_abstract).replace('\n',' ').replace('aogheaohtaope','\n\n'))
    elif talk.abstract:
        email_dict['abstract'] = "\n\n\nAbstract:\n\n" + delatex(re.sub('\n\s*\n','aogheaohtaope', talk.abstract).replace('\n',' ').replace('aogheaohtaope','\n\n'))
    else:
        email_dict['abstract'] = ''
        msg.attach(MIMEText(email_text_template.substitute(email_dict), 'plain', 'UTF-8'))
        msg.attach(MIMEText(email_html_template.substitute(email_dict), 'html', 'UTF-8'))
        file = open('emails/email-noabs_' + talk.date.strftime("%m-%d") + '.txt', 'w')
        file.write(str(msg))
        file.close()
        msg.set_payload([])
        msg.replace_header('To', config.organizer_email)
        msg.replace_header('Subject', "No abstract for " +talk.date.strftime("%A") + "'s talk")
        email_dict['extra_prefix'] = "Either add an abstract, run make_index{version}.py, then execute 'sendmail -t emails/email_" + talk.date.strftime("%m-%d") + ".txt' or execute 'sendmail -t emails/email-noabs_" + talk.date.strftime("%m-%d") + ".txt' to send the email without an abstract.\n\n "
    
    msg.attach(MIMEText(re.sub("<.*?>","",email_text_template.substitute(email_dict)), 'plain', 'UTF-8'))
    if talk.abstract:
        email_dict['abstract'] = '<br><br><p>' + email_dict['abstract'][3:].replace('\n\n','<br><br>') + '</p>'
    msg.attach(MIMEText(email_html_template.substitute(email_dict), 'html', 'UTF-8'))
    file = open('emails/email_' + talk.date.strftime("%m-%d") + '.txt', 'w')
    file.write(str(msg))
    file.close()


# creates a link to a Google calendar event
# can ONLY be called if talk has a 'speaker' entry
def makegooglelink(talk):
    l = ['http://www.google.com/calendar/event?action=TEMPLATE&text=', talk.speaker.text]
    if talk.title:
        l.append(': %s' % talk.title)
    dst = time.localtime((talk.date-epoch).total_seconds()).tm_isdst
    l.append('&dates=%s%d%s' % ((talk.date.strftime('%Y%m%dT'),talk.date.hour + local_timezone - dst,talk.date.strftime('%M00Z'))))
    end = talk.date + standard_duration
    l.append('/%s%d%s' % (end.strftime('%Y%m%dT'), end.hour + local_timezone - dst, end.strftime('%M00Z')))
    l.append('&sprop=MIT Topology Seminar&location=%s' % 'MIT ' + config.standard_room)
    return ''.join(l)

class MaybeLink:
    def __init__(self, text, url=None):
        self.text = text
        self.url = url
    def __str__(self):
        if self.url:
            return '<a href="%s">%s</a>' % (self.url, self.text)
        else:
            return self.text

class Talk:
    def __init__(self, date, reason = None, speaker = None, institutions = None, website = None, title = None, abstract = None, email_abstract = None, notice = None):
        self.date = date
        self.upcoming = date > datetime.today()
        self.name = date.strftime('%Y%m%d') + "-" + speaker # This is the name of the poster file.
        self.title = nonEmpty(title)
        self.abstract = nonEmpty(abstract)
        self.email_abstract = nonEmpty(email_abstract)
        self.notice = nonEmpty(notice)
        self.reason = nonEmpty(reason)
        if nonEmpty(speaker):
            # self.speaker might have a URL; self.speaker_name is just the name
            self.speaker_name = speaker
            self.speaker = MaybeLink(speaker, website)
            self.institutions = []
            for institution in institutions.split(";"):
                try:
                    self.institutions.append(institutionTable[sanitize_key(institution)])
                except KeyError:
                    self.institutions.append(MaybeLink(institution, ''))
                    print "--- Institution '%s' has no institution link in institutionTable.csv. Please add it." % institution.strip()
        else:
            self.speaker = None
            self.speaker_name = None

                
    def __str__(self):
        l = []
        l.append('<li class="talk">\n');
        # first the top info
        l.append('<ul class="meta">\n')
        l.append('<li class="date"><b>%s</b>%d</li>\n' % (self.date.strftime('%b %d'), self.date.year))
        if self.upcoming and self.speaker:
            # don't put a pdf icon if there is no poster
            if os.path.isfile("posters/%s.pdf" % self.name):
                l.append('<li class="poster"><a href="posters/%s.pdf" title="Download Poster"></a></li>\n' % self.name)
            l.append('<li class="calendar"><a title="Add to Google Calendar" href="%s"></a></li>\n' % makegooglelink(self))
        l.append('</ul>\n')

        # now the title and abstract, if we have them
        if self.reason:
            l.append('<h3>%s</h3>\n' % self.reason)
        elif self.speaker:
            institutions = self.institutions
            if len(institutions) == 1:
                institution = institutions[0]
            elif len(institutions) == 2:
                institution = str(institutions[0]) + " and " + str(institutions[1])
            else:
                last = institutions.pop()
                institution = ""
                for inst in institutions:
                    insitution = institution + str(inst) + ", "
                insitution = institution + "and " + str(inst)
            l.append('<h3 class="speaker">%s<span> (%s)</span></h3>\n' % (self.speaker, institution))
            if self.title and self.abstract:
                l.append('<h4 class="title"><label for="%s">\n'
                         '%s</label></h4>\n<input type="checkbox" id="%s" />'
                         '<label for="%s" class="plusminus"></label><div style="clear: both;"></div>\n' % (self.name,self.title,self.name,self.name))
            elif self.title:
                l.append('<h4>%s</h4><div style="clear: both;"></div>\n' % delatexquotes(self.title))
            if self.notice:
                l.append('<p class="notice">%s</p>\n' % self.notice)
            if self.abstract:
                l.append('<div class="abstract"><p>%s</p></div>\n' % delatexquotes(self.abstract).replace('\n\n','</p>\n<p>'))

        
        l.append('</li>\n\n\n')
        
        return ''.join(l)


def semester(t):
    d = t.date
    if d.month <= 5:
        return "Spring"
    elif d.month <= 8:
        return "Summer"
    else:
        return "Fall"

# translate latex accents \'e in talk t to html accents &eacute;
def convert_accents(t):
    vowels = ['a', 'e', 'i', 'o', 'u', 'y', 'A', 'E', 'I', 'O', 'U', 'Y']
    trans = [(r"\\'" + vowel, "&" + vowel + "acute;") for vowel in vowels]\
        + [(r"\\`" + vowel, "&" + vowel + "grave;") for vowel in vowels]\
        + [(r'\\"' + vowel, "&" + vowel + "uml;") for vowel in vowels]\
        + [(r"\\^" + vowel, "&" + vowel + "circ;") for vowel in vowels]\
        + [(r"\\~" + vowel, "&" + vowel + "tilde;") for vowel in vowels]\
        + [(r"\\aa ", "&aring;"), (r"\\ae ", "&aelig;"), (r"\\oe ", "&#156;")]\
        + [(r"\\o ", "&oslash;"), (r"\\O ", "&Oslash;"), (r"\\c c", "&ccedil;")]\
        + [(r"\\c{c}", "&ccedil;"), ("``", '"'), ("''", '"')]
    for pair in trans:
        t.speaker.text = re.sub(pair[0], pair[1], t.speaker.text)
    if t.institutions:
        for pair in trans:
            for institution in t.institutions:
                institution.url = re.sub(pair[0], pair[1], institution.url)
    if t.title:
        for pair in trans:
            t.title = re.sub(pair[0], pair[1], t.title)
    if t.abstract:
        for pair in trans:
            t.abstract = re.sub(pair[0], pair[1], t.abstract)


def makeoldpasttalks():
    talkReader = csv.DictReader(open('oldtalks.csv'))
    talks = []
    for row in talkReader:
        try:
            day = datetime.strptime(row['DATE'], '%Y/%m/%d')
            if row['ALTTIME'] != '':
                t = datetime.strptime(row['ALTTIME'], '%H:%M:%S').time()
            else:
                t = datetime.time(16, 30)
            d = datetime.combine(day, t)
        except ValueError:        
            if row['DATE'] != '':
                print 'Error:  "%s" is not a valid date' % row['DATE']
            continue
    
        if row['REASON'] != '':
            talks.append(Talk(date=d, reason=row['REASON']))
        elif row['SPEAKER'] != '':
            if row['INSTITUTION'] != '':
                talks.append(Talk(date=d, speaker=row['SPEAKER'],
                                  institutions=row['INSTITUTION'],
                                  website=row['WEBSITE'], title=row['TITLE'],
                                  abstract=row['ABSTRACT'], notice=row['SPECIAL']))
            else:
                print "Warning: row with date %s has no institution for the speaker %s" % (d.strftime("%m/%d/%Y"), row['SPEAKER'])
    
    
    map(convert_accents, talks)
    dategetter = lambda x: x.date
    talks.sort(key=dategetter, reverse=True)
    sem = ''
    past = []
    for talk in talks:
        season = semester(talk)
        cursem = season + " " + str(talk.date.year)
        if cursem != sem:
            sem = cursem
            past.append('</ul></div>\n\n')
            past.append('<div class="semester %s"><h2><label for="%s">%s</label></h2>\n' 
                        '<input type="checkbox" id="%s" /><label for="%s" class="plusminus semester_plusminus"></label>'
                        '<div style="clear: both;"></div>' % (season.lower(),sem,sem,sem,sem))
            past.append('<ul class="talks">\n')
        past.append(str(talk))
    
    # the first element of past is closing the previous semester, which never happened
    # the last element (closing the previous semester) doesn't exist
    past.append('</ul></div>\n\n')
    past.pop(0)
    past = ''.join(past)
    # and we want to expand the first semester
    past = past.replace(' blank', '', 1)
       
    file('oldpastseminars.html', 'w').write(past)


##############################################################################
##############################################################################
##############################################################################
##############################################################################
##############################################################################
##############################################################################

headerFooterTemplate = Template(file('headerfooter.template').read())

print "Reading data files"
# insert downloading stuff from Google here

instReader = csv.DictReader(open('institutions_new.csv'))
institutionTable = {}
for row in instReader:
    instKeys = row['KEYS'].split(";")
    instName = row["NAME"]
    institutionTable[sanitize_key(instName)] = MaybeLink(instName, row['LINK'])
    for instKey in instKeys:
        instKey = instKey.strip()
        if instKey != '':
            institutionTable[sanitize_key(instKey)] = MaybeLink(instName, row['LINK'])


# Before we parse the json file, we make some changes to allow multiline strings and a comment at the beginning (neither of which are allowed in json standard)
talkJson = open('talks.json')
jsonCommentLinesRemoved = 0
line = talkJson.readline()
# Remove initial lines that start with #, this is the comment header -- we won't handle comments anywhere else
while line[0]=='#':
    jsonCommentLinesRemoved += 1  # To fix the line number in ValueError when parsing json
    line = talkJson.readline()
talkStr = line + talkJson.read()

# Now handle multiline strings -- first we need to figure out when we're in a string, so we'll split by "
talkStr = talkStr.replace(r'\"','blargh an escaped quote') # But make sure not to count escaped quotes, we'll sub it back later. Hopefully no one will say 'blargh an escaped quote' in their abstract....
talkStrs = talkStr.split('"') 
talkStr = ''
i = 0
for subStr in talkStrs:
    i += 1
    if i % 2 == 0: # the even elements of this list are strings.
        # Escape the newlines, delete extra spaces around them, delete any \r's from that came from windows editors, and put the quotes back in
        subStr = '"' + '\\n'.join([x.strip(' ') for x in subStr.replace('\r','').split('\n')]) + '"' 
    talkStr = talkStr +  subStr 

# Escape backslashes (so that $\latex$ doesn't throw "error bad escape") but then don't escape the new lines.
talkStr = talkStr.replace('\\','\\\\').replace('\\\\n','\\n').replace('\t','\\t').replace('blargh an escaped quote','\\"')

try:
    talkTable = json.loads(talkStr)
except ValueError as e:
    msg = e[0]
    line_start = msg.find('line ')
    line_end = msg.find(' column')
    if (line_start != -1) and (line_end != -1):
        msg = msg[:line_start+5] + str(int(msg[line_start+5:line_end]) + jsonCommentLinesRemoved) + msg[line_end:]
    if msg[:21] == 'Expecting , delimiter':
        raise ValueError(msg + '\nDid you forget to escape a quote? Double quotes need to be printed as \\"'),None,sys.exc_info()[2]
    else:
        raise ValueError(msg)


talks = []
for sem in talkTable.values():
    for talk in sem:
       # try:
        day = datetime.strptime(talk['date'], '%Y/%m/%d')
        if 'alt_time' in talk:
            t = datetime.strptime(talk['alt_time'], '%H:%M').time()
        else:
            t = standard_time
        d = datetime.combine(day, t)
#        except ValueError:        
#            if talk.get('date','') != '':
#                print 'Error:  "%s" is not a valid date' % talk['date']
#            continue
    
        if 'cancellation_reason' in talk:
            talks.append(Talk(date=d, reason=talk['cancellation_reason']))
        elif talk.get('speaker','') != '':
            if talk.get('institution','') != '':
                talks.append(Talk(date=d, speaker=talk['speaker'],
                                  institutions=talk.get('institution',''),
                                  website=talk.get('website',''), title=talk.get('title',''),
                                  abstract=talk.get('abstract',''),
                                  email_abstract=talk.get('email_abstract',''),  
                                  notice=talk.get('notice','')))
            else:
                print "Warning: talk with date %s has no institution for the speaker %s" % (d.strftime("%m/%d/%Y"), talk['speaker'])



today = datetime.today()

dategetter = lambda x: x.date
upcoming = [talk for talk in talks if talk.date >= today]
upcoming.sort(key=dategetter)

print 'Generating posters'
map(makeposter, upcoming)

print 'Generating emails'
os.system("rm emails/*")
map(makeemail, upcoming)

print 'Generating upcoming talks page'
map(convert_accents, upcoming)
if upcoming:
    upcoming = map(str, upcoming)
    # we want to expand the next two talks
    upcoming = ''.join(upcoming[:2]).replace('"checkbox"', '"checkbox" checked') + ''.join(upcoming[2:])
    # Set up unicode for html
    upcoming = upcoming.encode('ascii', 'xmlcharrefreplace')
else:
    upcoming = "<b> There are no more talks this semester. Check back next semester.</b><br/><br/><br/>"

template = Template(file('index.template').read())
content = template.substitute(
    upcoming = upcoming, 
    contact_email = config.organizer_email,
    standard_day = config.standard_day, 
    standard_time = str((standard_time.hour - 1) % 12 + 1) + ":" +  str(standard_time.minute),
    standard_room = config.standard_room
)
raw = headerFooterTemplate.substitute(content = content, contact_email = config.organizer_email)
raw = raw.replace('"index_nav"','"index_nav" class="active"')
file('index.html', 'w').write(raw)


print 'Generating past talks page'

# for past talks we split them into semesters
pastlist = [talk for talk in talks if talk.date < today]
map(convert_accents, pastlist)
pastlist.sort(key=dategetter, reverse=True)
sem = ''
past = []
for talk in pastlist:
    season = semester(talk)
    cursem = season + " " + str(talk.date.year)
    if cursem != sem:
        sem = cursem
        past.append('</ul></div>\n\n')
        past.append('<div class="semester %s"><h2><label for="%s">%s</label></h2>\n' 
                    '<input type="checkbox" id="%s" /><label for="%s" class="plusminus semester_plusminus"></label>'
                    '<div style="clear: both;"></div>' % (season.lower(),sem,sem,sem,sem))
        past.append('<ul class="talks">\n')
    past.append(str(talk))



# the first element of past is closing the previous semester, which never happened
# the last element (closing the previous semester) doesn't exist
past.append('</ul></div>\n\n')
past.pop(0)
past = ''.join(past)
# and we want to expand the first semester
past = past.replace('"checkbox"', '"checkbox" checked', 1)

# Set up unicode for html
past = past.encode('ascii', 'xmlcharrefreplace')

pastold = file('oldpastseminars.html').read()

template = Template(file('pastseminars.template').read())
content = template.substitute(past = past, pastold = pastold, contact_email = config.organizer_email)
raw = headerFooterTemplate.substitute(content = content, contact_email = config.organizer_email)
raw = raw.replace('"past_nav"','"past_nav" class="active"')
file('pastseminars.html', 'w').write(raw)

print 'Generating links page'
template = Template(file('links.template').read())
content = template.substitute(contact_email = config.organizer_email, organizer_name = config.organizer_first_name + " " + config.organizer_last_name)
raw = headerFooterTemplate.substitute(content = content, contact_email = config.organizer_email)
raw=raw.replace('links_nav','"links_nav" class="active"')
file('links.html', 'w').write(raw)

######

# vim:expandtab
