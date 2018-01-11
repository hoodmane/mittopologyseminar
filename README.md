# How to organize the Topology Seminar:

## At the beginning of the semester:

- Email help@math.mit.edu and ask them to add your account to the topology group.
- ssh into runge.mit.edu and navigate to the directory `/math/www/docs/topology`.
- Change the contact info in `config.py` (the email MUST BE yourusername@mit.edu)
- Make sure yourusername@mit.edu is on the mit-topology google group. If it isn't, email Mike Hopkins and ask him to add you: mjh@math.harvard.edu
- Run `fix-permissions.sh`
- Make a new file for the new semester `seminar_data/year_season.json`, so for instance `2018_Spring.json` or `2018_Fall.json`.
- Haynes will send you a list of speakers and dates. Add the talk info to the json file for the current semester (see below for how to structure the file).  
- Run `make-index3.1.py` (with no arguments) to regenerate the main page and the past seminars page using the talk data in `talks.json`, generate the posters that are linked from the webpage, and the emails.
- If the speaker's institution isn't in `institutionTable.csv`, the script will complain to you and you will need to add the institution there.
  Check to make sure that it isn't already in there with a different abbreviation -- if it is, please add your favorite abbreviation to the list of abbreviations for that institution.

## During the semester:

- Whenever Haynes emails you titles, abstracts, or new speakers, add the new info to the json file and rerun `make-index3.1.py`
- Jon Harmon will automatically be emailed two weeks in advance of each seminar, and also whenever you make changes to talks that are happening in less than two weeks. There is a 10 minute delay before changes emails are sent to Jon, hopefully so that if you make a sequence of small changes all in a row, they will get combined into one email.
- There is a cronjob that automatically emails the list ( mit-topology@googlegroups.com ) two days before the seminar.
- If the talk is cancelled or changed you will likely need to email the list by hand.
- If you ever get permission related errors, run `fix-permissions.sh` again.

-----------------------

# The json file

## Overall structure:

The json file should be structured as a list of talks:
    ``` {javascript}
     [
        talk1,
        talk2,
        ...
    ]
    ```
    Each talk is an object structured as follows:
    ``` {javascript}
        {
            "date": "date1",
            "speaker": "speaker1",
            "institution": "speaker's institution",
            "website": "speaker's website's url",
            "title": "talk title",
            "abstract": "talk abstract"
        }
    ```
    There are more fields, which are detailed below.


## LaTeX in the json file:
- LaTeX markup works; macro definitions are local to each talk and should go in the "macros" field.
- In the emails, all dollar signs and backslashes will be deleted, otherwise LaTeX will be left as-is.
  You should define macros to make sure this produces a good result, for instance if the abstract uses
  `\mathcal{C}`, you should make a local macro `\def\C{\mathcal{C}}` and write `\C` so that in the email it will appear as just "C" rather than "mathcal{C}".
- If you want to see what the email looks like ahead of time to make sure that everything is right, run `make-index3.1.py --test-email` and it will send the email just to you.
- If this produces an unsatisfactory email, use the `email_abstract` field to specify by hand what the plaintext version of the abstract should look like.

- Double quotes should be escaped: \" e.g.,  `<a href=\"the url\">link text</a>`
- Use latex quotes ` ``...'' ` when the quotes are going to be printed (they will be substituted back to normal quotes where appropriate).
- Accents should be written using unicode: ö not \"o, é not \'e.
- Math should be written like `$\inf$`
- Passing an empty string to any talk field is treated in the same way as omitting the field.


## Common Fields 
A talk is a JSON object which will typically have the following fields:

- date:
  Every talk must have a date, formatted "year/month/day". Talks without dates will be ignored.

- speaker:
  The name of the speaker, formatted "Firstname Lastname". Talks without speakers will be ignored.

- institution:
  Every talk should have (at least one) institution.
  Multiple institutions should be separated by semicolons, e.g., `"University of Oslo; MIT"`.
  Each institution should appear as a name or key in institutionTable.csv which is a lookup table for the math department urls.
  (If for some reason the institution has no url, leave the url entry empty.)
  If you want the name of an institution to be displayed with a semicolon for some reason, you must define an abbreviation in institutionTable.

- website:
  The speaker's home webpage. If present, the speaker's name on the webpage will appear as a link to their homepage.

- title:
  The talk's title. Even if this title is absent, the talk entry will show up on the website with a blank title field.

- macros:
  Macro definitions that are local to this talk. Use liberally to make sure the email looks good. For instance, if `\mathcal{C}` is used, even if it's only used once,
  you should define `\C` to be `\mathcal{C}` by saying `"macros" : "\def\C{\mathcal{C}}"` and use `\C` in the abstract. 
  This way, instead of appearing as `mathcal{C}` in the email it will appear as `C`

- abstract:
  The talk's abstract, optional. Newlines in the abstract work the same way as in a Latex file -- a single newline does nothing, a blank line starts a new paragraph.
  All accented characters should be in unicode (don't use latex style accents). 

- email_abstract:
  The abstract is included in the email sent out to the topology mailing list. By default the way that the email is generated is by taking the abstract and
  deleting all backslashes and dollar signs. This can produce an unsatisfactory result when the original abstract contains complicated math. The email_abstract
  field specifies exactly how the abstract should be included in the email, usually by replacing the offensive math expressions with words.

## Less commonly used fields:

- no_email: Any nonempty value prevents any email from being sent for the talk. You will have to send your own by hand. Use this if something really weird happens (three talks in a day?
two talks in the same week on different days?) or if you want to customize the email for some reason. Note that if there are multiple talks on the same day,
putting this flag into ANY OF THEM suppresses the email for all of them.

- alt_weekday: If the talk is not on a monday, you must say e.g., '"alt_weekday": "Thursday"'. This is just to catch date typos.

- alt_time: An alternate time for the seminar, in 24 hour format hour:minute (other than standard_time defined in config.py, currently 16:30)

- alt_room: An alternate room for the seminar.

- change_reason: The reason the time or room has been changed. For example, "due to the Simon's lectures" or "because of the MIT holiday".

- notice: A special notice. This goes on the website and into the email (but not into the poster) if email_notice is not present. Note that a notice is automatically
generated on the website and the email is automatically updated if 'alt_time' or 'alt_room' is present.

- email_notice: A special notice, which only goes into the email. Overrides notice for the purpose of the email (but only if it's nonempty).

- cancellation_reason: The reason the talk is cancelled. Will appear in GIANT BOLD LETTERS on the website.


-----------------------


# Notes/ changelog:

- if you have a speaker, you must have an institution for the speaker
- requirements: python 2.7
- not valid date message will print if alternate time is formatted wrong

## Michael Donovan writes:
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

## Eva Belmont writes:
I modified `make-index2.py` to use mathjax instead of some tex-to-html converter
that doesn't support as many special characters; the new version is called
`make-index2.1.py`. It looks like someone already tried this before, and made the
opposite decision? Mathjax doesn't support LaTeX     textmode accents; see
`convert_accents()` in the script. The list of translations there isn't complete.

The bit about `MathJax.Hub.Configured();` is because of this:
https://groups.google.com/forum/#!msg/mathjax-users/J-36V22-G9Q/dG4i9vOdEK4J

I added `email.template` etc.

I messed with the poster template; I think it looks better now, but it does
mean that the posters starting in Fall 2015 have a different format than the
older ones. If the abstract is really long, you might have to adjust some of the
parameters in `poster.template`.

## Hood Chatham writes:
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


## TODO: 
- Document things more.
- Send no talk today email with `cancellation_reason` or generic one if no reason given but no talk given in between actual talks? 
- Send an extra email warning about late week talks? 
- Auto-detect `no_email` cases? 
- Send email to organizer telling them to write their own email(s) in no email cases?



