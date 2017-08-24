#!/usr/bin/python
contactemail=""

import re
import sys

if (sys.version_info[0],sys.version_info[1]) < (2,5):
    raise "This requires python version 2.5 or greater"

from datetime import datetime, date, time, timedelta
from string import Template
import csv
import os
from textwrap import fill

#os.chdir("/math/www/docs/topology")

# constants

# daylight savings time correction; when not in DST, set to 0
dst = 1
# for use on Google calendar link
location = 'MIT 2-131' # for use on Google calendar requests
duration = timedelta(hours=1, minutes=30)
# if we want mathml, change this to ttm and change extesions from html to xml
# we will also need to modify the templates with the same html-to-xml change
tex_converter = 'tth -u2'
extension = 'html'

def nonEmpty(x):
    if x == '':
        return None
    else:
        return x


postertemp = Template(file('poster.template').read())

def makeposters(talk):
    # if there is no talk we make no poster!
    if talk.reason:
        return
    # if there is no title there's no point in making a poster
    if not talk.title:
        return

    d = dict(speaker='', abstract='', institution='', title='')
    d['date'] = 0 #talk.date.strftime('%A, %B %-d')
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
    if talk.institution:
        d['institution'] = talk.institution.text
    if talk.abstract:
        d['abstract'] = talk.abstract
    d['contactemail']=contactemail
    raw = postertemp.substitute(d)
    try:
        file('posters/%s.tex' % talk.name, 'w').write(raw)
    except IOError:
        pass
    os.system('pdflatex -interaction=batchmode posters/%s.tex >/dev/null' % talk.name)
    os.system('mv %s.pdf posters/ && rm -f %s.*' % (talk.name, talk.name))
    os.system('chmod 755 posters/%s.pdf' % (talk.name))

# creates a link to a Google calendar event
# can ONLY be called if talk has a 'speaker' entry
def makegooglelink(talk):
    l = ['http://www.google.com/calendar/event?action=TEMPLATE&text=', talk.speaker.text]
    if talk.title:
        l.append(': %s' % talk.title)
    l.append('&dates=%s%d%s' % ((talk.date.strftime('%Y%m%dT'),talk.date.hour+5-dst,talk.date.strftime('%M00Z'))))
    end = talk.date + duration
    l.append('/%s%d%s' % (end.strftime('%Y%m%dT'), end.hour+5-dst, end.strftime('%M00Z')))
    l.append('&sprop=MIT Topology Seminar&location=%s' % location)
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
    def __init__(self, date, reason=None, speaker=None, institution=None, website=None, title=None, abstract=None, special=None):
        self.date = date
        self.upcoming = date > datetime.today()
        self.name = date.strftime('%Y%m%d')
        self.title = nonEmpty(title)
        self.abstract = nonEmpty(abstract)
        self.special = nonEmpty(special)
        self.reason = nonEmpty(reason)
        if nonEmpty(speaker):
            # self.speaker might have a URL; self.speaker_name is just the name
            self.speaker_name = speaker
            self.speaker = MaybeLink(speaker, website)
            try:
                self.institution = institutions[institution]
            except KeyError:
                self.institution = MaybeLink(institution, '')
        else:
            self.speaker = None
            self.speaker_name = None

                
    def __str__(self):
        l = []
        l.append('<li class=" hidden">\n');
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
            l.append('<h3>%s<span> (%s)</span></h3>\n' % (self.speaker, self.institution))
            if self.title and self.abstract:
                l.append('<h4><a href="javascript:void(0);" onclick="toggle(this);" title="toggle abstract">\n'
                         '%s</a></h4>\n' % self.title)
            elif self.title:
                l.append('<h4>%s</h4>\n' % self.title)
            if self.special:
                l.append('<p class="special">%s</p>\n' % self.special)
            if self.abstract:
                l.append('<div class="abstract"><p>%s</p></div>\n' % self.abstract)
        
        l.append('</li>\n\n\n')
        
        return ''.join(l)


def semester(t):
    d = t.date
    if d.month <= 5:
        return "Spring %d" % d.year
    elif d.month <= 8:
        return "Summer %d" % d.year
    else:
        return "Fall %d" % d.year

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
    if t.institution:
        for pair in trans:
            t.institution.url = re.sub(pair[0], pair[1], t.institution.url)
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

print "Reading data files"
# insert downloading stuff from Google here

instReader = csv.DictReader(open('institutions.csv'))
institutions = {}
for row in instReader:
    inst = row['INSTITUTION']
    if inst != '':
        institutions[inst] = MaybeLink(inst, row['LINK'])

talkReader = csv.DictReader(open('oldtalks.csv'))
talks = []
for row in talkReader:
    try:
        day = datetime.strptime(row['DATE'], '%Y/%m/%d')
        if row['ALTTIME'] != '':
            t = datetime.strptime(row['ALTTIME'], '%H:%M:%S').time()
        else:
            t = time(16, 30)
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
                              institution=row['INSTITUTION'],
                              website=row['WEBSITE'], title=row['TITLE'],
                              abstract=row['ABSTRACT'], special=row['SPECIAL']))
        else:
            print "Warning: row with date %s has no institution for the speaker" % d.strftime("%m/%d/%Y")

print 'Generating upcoming talks page'

today = datetime.today()

dategetter = lambda x: x.date

upcoming = [talk for talk in talks if talk.upcoming]
upcoming.sort(key=dategetter)
map(makeposters, upcoming)
map(convert_accents, upcoming)
empty_upcoming = False
if upcoming:
    next_talk = upcoming[0]
    upcoming = ''.join(map(str, upcoming))
    # and we want to expand the next two talks
    upcoming = upcoming.replace(' hidden', '', 2)
else:
    empty_upcoming = True
    upcoming = "<b> There are no more talks this semester. Check back next semester.</b><br/><br/><br/>"

print 'Generating past talks page'

# for past talks we split them into semesters
pastlist = [talk for talk in talks if talk.date < today]
map(convert_accents, pastlist)
pastlist.sort(key=dategetter, reverse=True)
sem = ''
past = []
for talk in pastlist:
    cursem = semester(talk)
    if cursem != sem:
        sem = cursem
        past.append('</ul></div>\n\n')
        past.append('<div class="semester blank"><h2><a href="javascript:void(0);" onclick="togglesem(this)" title="toggle talks">%s</a></h2>\n' % sem)
        past.append('<ul class="talks">\n')
    past.append(str(talk))

# the first element of past is closing the previous semester, which never happened
# the last element (closing the previous semester) doesn't exist
past.append('</ul></div>\n\n')
past.pop(0)
past = ''.join(past)
# and we want to expand the first semester
past = past.replace(' blank', '', 1)

template = Template(file('index.template').read())
raw = template.safe_substitute(dict(upcoming=upcoming,contactemail=contactemail))
file('index.%s' % extension, 'w').write(raw)

template = Template(file('pastseminars.template').read())
raw = template.substitute(dict(past=past,contactemail=contactemail,pastold=""))
file('pastseminars.%s' % extension, 'w').write(raw)

quit()
if not empty_upcoming:
    template = Template(file('email.template').read())
    raw = template.substitute(abstract=next_talk.abstract, title=next_talk.title,
            speaker=next_talk.speaker_name, day=next_talk.date.strftime("%A"),
            date=0)#next_talk.date.strftime("%B %-d"),contactemail=contactemail)
    file('email.txt', 'w').write(raw)

# vim:expandtab
