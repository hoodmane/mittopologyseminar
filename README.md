### How to organize the Topology Seminar:

##### At the beginning of the semester:

- Email help@math.mit.edu and ask them to add your account to the topology group
- ssh into runge.mit.edu and navigate to the directory `/math/www/docs/topology`.
- Change the contact info in `config.py` (the email MUST BE yourusername@mit.edu)
- Make sure yourusername@mit.edu is on the mit-topology google group. If it isn't, email Mike Hopkins and ask him to add you: mjh@math.harvard.edu
- Run `fix-permissions.sh`. Do this again if you have any permission problems.
- Haynes will send you a list of speakers and dates. Add the talk info to `talks.json`.
  `talks.json` is structured like:
    ~~~~
     {
       "oldsemester1" : [ talk1, talk2, ...,  talkn ],
       "oldsemester2" : [ talk1, talk2, ...,  talkn ],
       ...
     }
    ~~~~
  You should add above `oldsemester1` the following (you'll have to google all of the speakers to find their websites):
    ~~~~
    "Fall/Spring current_year" : [
        {
            "date": "date1",
            "speaker": "speaker1",
            "institution": "speaker's institution",
            "website": "speaker's website's url",
            "title": "",
            "abstract": ""
        },
        ... more talks here
    ],
    ~~~~
  Read the comment at the top of `talks.json` for a description of the fields for each talk.

- Run `make-index3.1.py` (with no arguments) to regenerate the main page and the past seminars page using the talk data in `talks.json`, generate the posters that are linked from the webpage, and the emails.
- If the speaker's institution isn't in `institutionTable.csv`, the script will complain to you and you will need to add the institution there.
  Check to make sure that it isn't already in there with a different abbreviation -- if it is, please add your favorite abbreviation to the list of abbreviations for that institution.

##### During the semester:

- Whenever Haynes emails you titles, abstracts, or new speakers, add the new info to talks.json and rerun `make-index3.1.py`
- Jon Harmon will automatically be emailed two weeks in advance of each seminar, and also whenever you make changes to talks that are happening in less than two weeks. There is a 10 minute delay before changes emails are sent to Jon, hopefully so that if you make a sequence of small changes all in a row, they will get combined into one email.
- There is a cronjob that automatically emails the list ( mit-topology@googlegroups.com ) two days before the seminar.
- If the talk is cancelled or changed you will likely need to email the list by hand.

##### Notes on LaTeX in `talks.json`:
- LaTeX markup works; macro definitions are local to each talk and should go in the "macros" field.
- In the emails, all dollar signs and backslashes will be deleted, otherwise LaTeX will be left as-is.
  You should define macros to make sure this produces a good result, for instance if the abstract uses
  `\mathcal{C}`, you should make a local macro `\def\C{\mathcal{C}}` and write `\C` so that in the email it will appear as just "C" rather than "mathcal{C}".
- If you want to see what the email looks like ahead of time to make sure that everything is right, run `make-index3.1.py --test-email` and it will send the email just to you.
- If this produces an unsatisfactory email, use the `email_abstract` field to specify by hand what the math-free version of the abstract should look like.

-----------------------

#### Notes/ changelog:

- if you have a speaker, you must have an institution for the speaker
- requirements: python 2.7
- not valid date message will print if alternate time is formatted wrong

###### Michael Donovan writes:
1. if you get an error message like
  ~~~~
  Traceback (most recent call last):
    File "make-index2.py", line 189, in <module>
      day = datetime.strptime(row['DATE'], '%Y/%m/%d')
  KeyError: 'DATE'
  ~~~~
it is likely to be because talks.csv has been saved by your editor as a
UTF-8 with BOM. The BOM is three bytes at the start of the file which get
misconstrued as part of the `DATE` key, killing the program. Use a decent
editor like Notepad++ to change the encoding of `talks.csv` to ANSI.
2. I added the line `os.system('chmod 755 posters/%s.pdf' % (talk.name))`
in order to automatically give the posters the correct permissions.
I wonder if the previous organisers did this manually.

###### Eva Belmont writes:
I modified `make-index2.py` to use mathjax instead of some tex-to-html converter
that doesn't support as many special characters; the new version is called
`make-index2.1.py`. It looks like someone already tried this before, and made the
opposite decision? Mathjax doesn't support latex textmode accents; see
`convert_accents()` in the script. The list of translations there isn't complete.

The bit about `MathJax.Hub.Configured();` is because of this:
https://groups.google.com/forum/#!msg/mathjax-users/J-36V22-G9Q/dG4i9vOdEK4J

I added `email.template` etc.

I messed with the poster template; I think it looks better now, but it does
mean that the posters starting in Fall 2015 have a different format than the
older ones. If the abstract is really long, you might have to adjust some of the
parameters in `poster.template`.

###### Hood Chatham writes:
I replaced `talks.csv` with `talks.json` because there are lots of rare optional fields,
so it's more appropriate to have named fields. This way not every entry has to have
exactly the right number of commas in a row e.g., `2016/12/12,,,,"Ismar Volic` and
also since the abstract is usually many lines long that doesn't work naturally in a csv file.

I consolidated all of the stuff that a new organizer will certainly need to change in `config.py`

I messed around with the representation of the abstracts to fix the behavior of backslashes and newlines as follows:
 
 1. Newlines behave like they do in LaTeX -- a single newline has no effect, two newlines in a row create a new paragraph
 2. `\"` represents an escaped quote
 3. `\anythingelse` represents a LaTeX command

I made the website work without javascript by using some css magic. To be clear,
only the foldy-thingies for the abstract and semesters work without javascript, the math will just display as
raw TeX input.

I automated the email sending process. If the talk has all of its key fields (`speaker`, `title`, `abstract`),
then on Saturday morning it will send an appropriate email to the list. If not all of these fields are
filled out, it will send a reminder email to just the organizer to rectify the situation. The automated email
fills out it's `From:` field with `organizer_email`, which must be `something@mit.edu`. You also must be subscribed
to the topology list through `something@mit.edu`


###### TODO: 
- Document things more.
- Send no talk today email with `cancellation_reason` or generic one if no reason given but no talk given in between actual talks? 
- Send an extra email warning about late week talks? 
- Auto-detect `no_email` cases? 
- Send email to organizer telling them to write their own email(s) in no email cases?



