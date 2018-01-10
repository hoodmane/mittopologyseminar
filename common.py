# This file consists of stuff used both by make-juvitop.py and make-index.py
# hence the name "common." Don't make changes without checking that both still work.

import sys
import os
import subprocess
import threading
import argparse

from datetime import datetime, date, timedelta
import time

from uuid import uuid1
import unicodedata
import re
import csv  # For reading InstitutionTable and old talk tables
import json # For reading the talk files
import pickle # For serializing messages

# HTML escaping
from HTMLParser import HTMLParser
import cgi

try:
   import jinja2
except ImportError:
   os.system("pip install --user jinja2")
   import jinja2

try:
    from unidecode import unidecode
except ImportError:
    os.system("pip install --user unidecode")
    from unidecode import unidecode

latexJinjaEnv = jinja2.Environment(
	block_start_string = '\BLOCK{',
	block_end_string = '}',
	variable_start_string = '\VAR{',
	variable_end_string = '}',
	comment_start_string = '\#{',
	comment_end_string = '}',
	line_statement_prefix = '%%',
	line_comment_prefix = '%#',
	trim_blocks = True,
	autoescape = False,
	loader = jinja2.FileSystemLoader('templates')
)


try:
   import markdown
except ImportError:
   os.system("pip install --user markdown")
   import markdown


# Email things
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
smtp = smtplib.SMTP("outgoing.mit.edu")


if (sys.version_info[0],sys.version_info[1]) < (2,5):
    raise "This requires python version 2.5 or greater"
reload(sys)
sys.setdefaultencoding("utf-8")

if 'topology' not in subprocess.check_output('id -G -n', shell = True).split():
    print 'You must be in the topology group to use this program. Email help@math.mit.edu and ask them to add you to the topology group.'

os.umask(0002) # Make files with group write privileges.

scriptname = __file__

local_timezone = time.timezone / 60 / 60 # get the current time zone offset, ignoring daylight saving time (given in seconds, divide by 60 twice to get hours)
epoch = datetime.fromtimestamp(0) # For converting datetime object to time object (time constructor takes seconds since Jan 1st 1970) for finding out about daylight saving time.
    



### IO / System commands
# All of the direct reading and writing is here so that we can make sure to handle
# writing files correctly (we want to update the owner and make sure to chmod g+w them)

def readFile(path):
   tempFile = file(path, 'r')
   ret = tempFile.read()
   tempFile.close()
   return ret

def writeFile(path, contents):
   # Remove the file first to make sure that the owner of the file ends up being the
   # current organizer so that chown doesn't fail.
   os.system("rm %s 2> /dev/null" % path)
   fd = os.open(path, os.O_WRONLY | os.O_CREAT)
   os.write(fd, contents)
   os.close(fd)


def latexPoster(name, contents):
   writeFile("posters/%s.tex" % name, contents)
   os.system('lualatex -interaction=batchmode "posters/%s.tex" >/dev/null' % name)
   os.system('mv "%s.pdf" posters/ && rm -f "%s."*' % (name, name))
   #os.system("chmod o+r posters/%s.pdf" % name)


### String sanitization commands

placeholder_string = str(uuid1()) # Unique string 

# This makes sure that two keys don't fail to match because of capitalization, spelling, accents, similar stuff.
# convert string to lowercase and remove accents
def sanitize_key(input_str):
    input_str = re.sub(r"\\.","",input_str).strip().lower().replace("the ","")
    # remove accents from unicode characters
    nkfd_form = unicodedata.normalize('NFKD', unicode(input_str.lower()))
    return u"".join([c for c in nkfd_form if not unicodedata.combining(c)])

def delatex(str):
    return convert_quotes(str).replace("\\infty",u"\u221e").replace("\\infinity",u"\u221e").replace("\\","").replace("$","") # \u221e is infinity sign

def convert_quotes(string):
    return string.replace('``','"').replace("`","'").replace("''",'"')

# Turn unicode characters into closest nonunicode equivalent, delete characters that don't end up being alphanumeric, or ._-, turn spaces into dashes
def sanitizeFileName(str):
    keepcharacters = (' ','.','_','-')
    return "".join(c for c in unidecode(unicode(str)) if c.isalnum() or c in keepcharacters).rstrip().replace(' ','-')

class EscapeHTMLParser(HTMLParser,object):
    def handle_starttag(self, tag, attrs): 
        str = self.get_starttag_text()
        i = str.rfind("<")
        self.storedMarkup += cgi.escape(str[:i]) + str[i:]
        
    def handle_endtag(self, tag): 
        self.storedMarkup += "</" + tag + ">"
        
    def handle_data(self, data):
        self.storedMarkup+=cgi.escape(data)

    def handle_entityref(self,name):
        self.storedMarkup += "&%s;" % name
    
    def handle_charref(self,name):    
        self.storedMarkup += "&#%s;" % name        
    
    def escape(self,str):
        self.storedMarkup = ""
        self.feed(str)
        return self.storedMarkup

escapeHTMLParser = EscapeHTMLParser()

# We want to ignore single linebreaks and turn blank lines into new paragraphs, as appropriate for html or plaintext respectively.
def paragraphs_to_html(string):   
   return escapeHTMLParser.escape('<p>\n' + re.sub('\n\s*\n', '\n</p>\n\n<p>\n', string) + '\n</p>\n')

# Text also shouldn't have any html tags, so we delete them
def paragraphs_to_text(string):
   return "\n\n" + re.sub("<[^$]*?>","", delatex(re.sub('\n\s*\n',placeholder_string, string).replace('\n',' ').replace(placeholder_string,'\n\n')))

    


## Handle links
# A link is represented like: [reference text] or ['reference' text]
# References cannot contain single quotes ' 
# An unquoted reference cannot contain spaces (they will end the link) or closed brackets, quoted references can handle either
# If the reference is of the form "file.pdf" (no forward slashes) then the path "notes_{current_semester}/" will be added
# If the reference contains at most one dots, it will be interpreted as a relative reference (relative to /math/docs/www/topology)
# If the reference contains two or more dots (e.g., somedomain.com/path/file.ext) it will add "http://" the begininng 
# unless it already started with "something://"

# The regex all match the expression [<possible whitespace> reference <whitespace> text <possible whitespace>]
# The text is defined as one or more characters, no ]'s. This is the same every time.
# link_template stores the part that's the same every time, which is everything but the reference.

link_file_only        = re.compile("^[^/]*$") # To see that it's only the file name, we require there be no /'s
link_rel              = re.compile("^((?:[^'\. \]]*\.?){1,2})$") # To be relative, we check that there is at most one .
link_full_http        = re.compile("^\w*://.*$") 


class myLinkPattern(markdown.inlinepatterns.LinkPattern):
    def sanitize_url(self, url):
	if link_file_only.match(url):
            return self.markdown.notes_path + url
        elif link_rel.match(url):
            return self.markdown.base_path + url
        elif link_full_http.match(url):
            return url
        else:
            return "http://"+url

class JuvitopExtension(markdown.Extension):
    """ Extension for Python-Markdown. """

    def extendMarkdown(self, md, md_globals):
        md.inlinePatterns['link'] = myLinkPattern(markdown.inlinepatterns.LINK_RE, md)


myExtension = JuvitopExtension()
mymarkdown = markdown.Markdown(extensions=[myExtension])




class MaybeLink:
    def __init__(self, text, url=None):
        self.text = text
        self.url = url
    def __str__(self):
        if self.url:
            return '<a href="%s">%s</a>' % (self.url, self.text)
        else:
            return self.text
            
def getSeason(d):
    if d.month <= 5:
        return "Spring"
    elif d.month <= 8:
        return "Summer"
    else:
        return "Fall"
        

### Simple email handling stuff

def promptSend(target_email):
    ans = raw_input('You sure you want to send the email to %s? You can have a test email send to yourself first by running "./make-index3.1.py --test-email". (yes/no): ' % target_email) 
    while ans not in ['yes','no']:
        ans = raw_input('yes or no? ')
    return ans == 'yes'

def sendEmail(msg):
    smtp.sendmail(msg['From'], msg['To'], msg.as_string())

    


# I made a bunch of small "extensions" to the JSON standard:
#
#   One long comment allowed at the top of the file (to explain how the fields work, etc).
#   Fix the line numbers in errors to reflect the actual linenumber (counting the lines deleted for the comment).
#   Allow strings to have newlines in them.
#   Treat newlines in strings like to LaTeX paragraphs (single ones go away, two in a row makes a paragraph).
#   Automatically escape backslashes, so that people don't have to type \\\\acommand all the time. 
#   Except for \n, which counts as a newline character (this should maybe change)
#   Delete trailing commas before } or ]. (These are JSON errors, but are easy to fix and make it easier to avoid forgetting to have enough commas.)

def processJSON(fileName):
    talkJson = open(fileName)
    jsonCommentLinesRemoved = 0
    line = talkJson.readline()
    # Remove initial lines that start with #, this is the comment header -- we won't handle comments anywhere else
    while line[0]=='#':
        jsonCommentLinesRemoved += 1  # To fix the line number in ValueError when parsing json
        line = talkJson.readline()
    talkStr = line + talkJson.read()
    talkJson.close()
    
    # Now handle multiline strings -- first we need to figure out when we're in a string, so we'll split by "
    talkStr = talkStr.replace(r'\"',placeholder_string) # But make sure not to count escaped quotes, we'll sub it back later. Hopefully no one will say 'blargh an escaped quote' in their abstract....
    talkStrs = talkStr.split('"') 
    
    # Check whether there are common syntax errors -- missing comma or unescaped quote
    for i in range(2,len(talkStrs),2):
	s = talkStrs[i].strip()
	if len(s)==0 or s[0] not in ('}',']',',',':'): # After every closing quote, the next nonwhitespace character should be one of these
	   # If it isn't, count row and column of offending quote to make error message
	   newlines = jsonCommentLinesRemoved + 1 # When we count up all the newlines we get (current line - 1), so need to add 1 here
	   for j in range(0,i):
	      n=talkStrs[j].count('\n') # Count newline characters to determine line number
	      if n>0: # Also find index that contains most recent newline (for counting column)
		k=j 
	      newlines+=n
           # Now count column
	   col = len(('\n'+talkStrs[k]).rsplit('\n',1)[-1]) + 1 # Find everything after the most recent newline
           for s in talkStrs[k+1:i]:
	      col+=len(s) # add up everything in column
           col += (i-k)/2 *2 if i-k>1 else 1  # add in the quote characters
           raise ValueError('Expecting "," delimiter: line %s column %s (after "%s")\nEither you forgot a comma or to escape a quote. Double quotes need to be printed as \\"' % (newlines, col,' '.join(('  '+talkStrs[i-1]).rsplit(None,5)[1:])))

    # We strip initial spaces because we want to format the JSON file nicely, with indentation and stuff, but we don't want all of the initial spaces to creep in.
    # Problem is, in markdown indentation has special meaning. The solution here: if a line starts with three dots, remove those three dots. Subsequent spaces are 
    # kept.
    for i in range(1,len(talkStrs),2):
        talkStrs[i] = '\\n'.join([x.strip(' ').strip('...') for x in talkStrs[i].replace('\r','').split('\n')])

    talkStr = '"'.join(talkStrs)
    
    # Escape backslashes (so that $\latex$ doesn't throw "error bad escape") but then don't escape the new lines.
    talkStr = talkStr.replace('\\','\\\\').replace('\\\\n','\\n').replace('\t','').replace(placeholder_string,'\\"')
    # Delete trailing commas (any comma that comes immediately before a } or ] )
    talkStr = re.sub(',(\s*[}\]])','\\1',talkStr)
    
    try:
        talkTable = json.loads(talkStr)
    except ValueError as e:
        msg = e[0]
        line_start = msg.find('line ')
        line_end = msg.find(' column')
        if (line_start != -1) and (line_end != -1):
            msg = msg[:line_start+5] + str(int(msg[line_start+5:line_end]) + jsonCommentLinesRemoved) + msg[line_end:]
        if re.match("Expecting ?',?' delimiter",msg) != -1:
            raise ValueError(msg + '\nDid you forget to escape a quote? Double quotes need to be printed as \\"'),None,sys.exc_info()[2]
        else:
            raise ValueError(msg)
    return talkTable
