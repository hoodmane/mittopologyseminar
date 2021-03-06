emergency_email_shutoff = False # Change to True if the mailer goes haywire!


organizer_first_name = "Andrew"
organizer_last_name = "Senger"
organizer_email = "senger@mit.edu"  # This must be your @mit.edu email.

webmaster_email = "hood@mit.edu"
target_email = "mit-topology@googlegroups.com" # "hood_test@googlegroups.com" #


standard_weekday = "Monday"
standard_time = "16:30" # Default time for the seminar in 24 hr format
standard_room = "2-131"
standard_duration = "1:00" # Default duration, "hrs:minutes"

working_directory = "/math/www/docs/topology" 
sendEventEmails = True
eventNoticeEmailSource = "topology-seminar-events@math.mit.edu"
eventNoticeEmailTarget = "harmonjo@mit.edu"




testMode = False
if(testMode):
    target_email = "hood_test@googlegroups.com"
    sendJonEmails = False

timezone = "America/New_York"
