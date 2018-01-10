### How to structure

Double quotes should be escaped: \" e.g.,  <a href=\"the url\">link text</a>
Use latex quotes ``...'' when the quotes are going to be printed (they will be substituted back to normal quotes in the email).
Accents should be written using unicode: ö not \"o, é not \'e.
Math should be written like $\inf$

This file contains a single object, with one field per semester.
These fields each contain the list of talks for that semester. A talk is an object which will typically have the following fields:

date:
  Every talk must have a date, formatted "year/month/day", talks without dates will be ignored.

speaker:
  Every talk must have a speaker, talks without speakers will be ignored.

institution:
  Every talk should have (at least one) institution.
  Multiple institutions should be separated by semicolons, e.g., "University of Oslo; MIT".
  Each institution should appear as a name or key in institutionTable.csv which is a lookup table for the math department urls.
  (If for some reason the institution has no url, leave the url entry empty.)
  If you want the name of an institution to be displayed with a semicolon for some reason, you must define an abbreviation in institutionTable.

website:
  The speaker's home webpage. If present, the speaker's name on the webpage will appear as a link to their homepage.

title:
  The talk's title

macros:
  Macro definitions that are local to this talk. Use liberally to make sure the email looks good. For instance, if a \mathcal{C} is used, even if it's only used once,
  you should define \C to be \mathcal{C} and use \C. This way, in the email instead of appearing as "mathcal{C}" it will appear as "C"

abstract:
  The talk's abstract, optional. Newlines in the abstract work the same way as in a Latex file -- a single newline does nothing, a blank line starts a new paragraph.
  All accents should be in unicode.

email_abstract:
  The abstract is included in the email sent out to the topology mailing list. By default the way that the email is generated is by taking the abstract and
  deleting all backslashes and dollar signs. This can produce an unsatisfactory result when the original abstract contains complicated markup. The email_abstract
  field specifies exactly how the abstract should be included in the email, usually by breaking up the offensive expressions with words.


The following are some less commonly used fields:

no_email: Any nonempty value prevents any email from being sent for the talk. You will have to send your own by hand. Use this if something really weird happens (three talks in a day?
two talks in the same week on different days?) or if you want to customize the email for some reason. Note that if there are multiple talks on the same day,
putting this flag into ANY OF THEM suppresses the email for all of them.

alt_weekday: If the talk is not on a monday, you must say e.g., '"alt_weekday": "Thursday"'. This is just to catch date typos.

alt_time: An alternate time for the seminar, in 24 hour format hour:minute (other than standard_time defined in config.py, currently 16:30)

alt_room: An alternate room for the seminar.

change_reason: The reason the time or room has been changed. For example, "due to the Simon's lectures" or "because of the MIT holiday".

notice: A special notice. This goes on the website and into the email (but not into the poster) if email_notice is not present. Note that a notice is automatically
generated on the website and the email is automatically updated if 'alt_time' or 'alt_room' is present.

email_notice: A special notice, which only goes into the email. Overrides notice for the purpose of the email (but only if it's nonempty).

cancellation_reason: The reason the talk is cancelled. Will appear in GIANT BOLD LETTERS on the website.

Passing an empty string to any talk field is treated in the same way as omitting the field.
