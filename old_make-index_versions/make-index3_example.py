#!/usr/bin/python

import sys
import os
from datetime import datetime, date, time, timedelta

import re
import csv
import json
import unicodedata
from string import Template

from config import *

standard_time = datetime.strptime(standard_time, '%H:%M').time()
standard_duration = timedelta(hours=int(standard_duration.split(":")[0]), minutes=int(standard_duration.split(":")[1]))

if (sys.version_info[0],sys.version_info[1]) < (2,5):
    raise "This requires python version 2.5 or greater"
reload(sys)
sys.setdefaultencoding("utf-8")

os.chdir("/math/www/docs/topology")

# constants

# daylight savings time correction; when not in DST, set to 0
dst = 1
# if we want mathml, change this to ttm and change extension from html to xml
# we will also need to modify the templates with the same html-to-xml change
tex_converter = 'tth -u2'
extension = 'html'

def nonEmpty(x):
    if x == '':
        return None
    else:
        return x
        
# convert string to lowercase and remove accents
def sanitize_key(input_str):
    input_str=re.sub(r"\\.","",input_str).strip().lower().replace("the ","")
    # remove accents from unicode characters
    nkfd_form = unicodedata.normalize('NFKD', unicode(input_str.lower()))
    return u"".join([c for c in nkfd_form if not unicodedata.combining(c)])


postertemp = Template(file('poster.template').read())

def makeposter(talk):
    # if there is no talk we make no poster!
    if talk.reason:
        return
    # if there is no title there's no point in making a poster
    if not talk.title:
        return

    d = dict(speaker='', abstract='', institution='', title='', contact_email = organizer_email, room = standard_room)
    d['date'] = talk.date.strftime('%A, %B %-d')
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
        d['abstract'] = talk.abstract

    raw = postertemp.substitute(d)
    try:
        file('posters/%s.tex' % talk.name, 'w').write(raw)
    except IOError:
        pass
    os.system('pdflatex -interaction=batchmode "posters/%s.tex" >/dev/null' % talk.name)
    os.system('mv "%s.pdf" posters/ && rm -f "%s."*' % (talk.name, talk.name))
    os.system('chmod 755 "posters/%s.pdf"' % (talk.name))

emailtemp = Template(file('email.template').read())

def makeemail(talk):
    # If there's no talk, don't make an email (maybe make an email clarifying that the talk has been cancelled?)
    if talk.reason:
        return
    # If there's no title, make an email to organizer complaining
    if not talk.title:
        file('example_emails/email_' + talk.date.strftime("%m-%-d") + '.txt', 'w').write( \
            "To: " + organizer_email + "\n" \
            "Subject: No title for " + talk.date.strftime("%A") + "'s talk" \
            "\nPlease add a title and hopefully an abstract for " + talk.speaker_name + "'s talk, run make-index{version}.py and " \
            "then execute 'sendmail -t emails/email_" + talk.date.strftime("%m-%-d") + "" \
            "' or 'sendmail -t emails/email-noabs_" + talk.date.strftime("%m-%-d")+"\n"
        )
        return
    
    email = dict(                
        name = organizer_first_name,
        recipient = target_email,
        subject = "MIT topology seminar: " + talk.speaker_name,
        title = talk.title.replace("\\","").replace("$",""),
        speaker = talk.speaker_name, 
        day = talk.date.strftime("%A"),
        date = talk.date.strftime("%B %-d"),
        time = talk.date.strftime("%l:%M").strip(),
        room = standard_room
    )
    
    if talk.abstract:  # if there is an abstract, just make an email to the google group
        email['abstract'] = "\n\n\nAbstract:\n\n" + talk.abstract.replace("\\","").replace("$","")
    else:
        email['abstract'] = ""
        file('example_emails/email-noabs_' + talk.date.strftime("%m-%-d") + '.txt', 'w').write(emailtemp.substitute(email))
        email['recipient'] = organizer_email
        email['subject'] = "No abstract for " +talk.date.strftime("%A") + "'s talk \nEither add an abstract, run make_index{version}.py, then execute 'sendmail -t emails/email_" + talk.date.strftime("%m-%-d") + "' or execute 'sendmail -t emails/email-noabs_" + talk.date.strftime("%m-%-d") + "' to send the email without an abstract.\n\n "

    file('example_emails/email_' + talk.date.strftime("%m-%-d") + '.txt', 'w').write(emailtemp.substitute(email))


# creates a link to a Google calendar event
# can ONLY be called if talk has a 'speaker' entry
def makegooglelink(talk):
    l = ['http://www.google.com/calendar/event?action=TEMPLATE&text=', talk.speaker.text]
    if talk.title:
        l.append(': %s' % talk.title)
    l.append('&dates=%s%d%s' % ((talk.date.strftime('%Y%m%dT'),talk.date.hour+5-dst,talk.date.strftime('%M00Z'))))
    end = talk.date + standard_duration
    l.append('/%s%d%s' % (end.strftime('%Y%m%dT'), end.hour+5-dst, end.strftime('%M00Z')))
    l.append('&sprop=MIT Topology Seminar&location=%s' % 'MIT ' + standard_room)
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
    def __init__(self, date, reason=None, speaker=None, institutions=None, website=None, title=None, abstract=None, notice=None):
        self.date = date
        self.upcoming = date > datetime.today()
        self.name = date.strftime('%Y%m%d') + "-" + speaker # This is the name of the poster file.
        self.title = nonEmpty(title)
        self.abstract = nonEmpty(abstract)
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
            l.append('<h3>%s<span> (%s)</span></h3>\n' % (self.speaker, institution))
            if self.title and self.abstract:
                l.append('<h4><label for="%s">\n'
                         '%s</label></h4>\n<input type="checkbox" id="%s" />'
                         '<label for="%s" class="plusminus"></label><div style="clear: both;"></div>\n' % (self.name,self.title,self.name,self.name))
            elif self.title:
                l.append('<h4>%s</h4>\n' % self.title)
            if self.notice:
                l.append('<p class="notice">%s</p>\n' % self.notice)
            if self.abstract:
                l.append('<div class="abstract"><p>%s</p></div>\n' % self.abstract)
        
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


talkJson = open('example.json')
line = talkJson.readline()
while line[0]=="#":
    line = talkJson.readline()
talkTable = json.loads(line + talkJson.read())

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
                                  abstract=talk.get('abstract',''), notice=talk.get('notice','')))
            else:
                print "Warning: talk with date %s has no institution for the speaker %s" % (d.strftime("%m/%d/%Y"), talk['speaker'])



today = datetime.today()

dategetter = lambda x: x.date
upcoming = [talk for talk in talks if talk.date >= today]
upcoming.sort(key=dategetter)

print 'Generating posters'
map(makeposter, upcoming)

print 'Generating emails'
os.system("rm example_emails/*")
map(makeemail, upcoming)

print 'Generating upcoming talks page'
map(convert_accents, upcoming)
if upcoming:
    upcoming = ''.join(map(str, upcoming))
    # and we want to expand the next two talks
    upcoming = upcoming.replace('"checkbox"', '"checkbox" checked', 2)
else:
    upcoming = "<b> There are no more talks this semester. Check back next semester.</b><br/><br/><br/>"

template = Template(file('index.template').read())
content = template.substitute(upcoming = upcoming, contact_email=organizer_email,standard_day = standard_day, standard_time = standard_time.strftime("%l:%M").strip(), standard_room = standard_room)
raw = headerFooterTemplate.substitute(content = content, contact_email = organizer_email)
raw=raw.replace('"index_nav"','"index_nav" class="active"')
file('example_index.%s' % extension, 'w').write(raw)


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
                    '<input type="checkbox" id="%s" /><label for="%s" class="plusminus"></label>'
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

pastold = ""

template = Template(file('pastseminars.template').read())
content = template.substitute(past = past, pastold = pastold, contact_email = organizer_email)
raw = headerFooterTemplate.substitute(content = content, contact_email = organizer_email)
raw=raw.replace('"past_nav"','"past_nav" class="active"')
file('example_pastseminars.%s' % extension, 'w').write(raw)

######

# vim:expandtab
