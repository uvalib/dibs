'''
email.py: email utilities for DIBS

Copyright
---------

Copyright (c) 2021-2022 by the California Institute of Technology.  This code
is open-source software released under a 3-clause BSD license.  Please see the
file "LICENSE" for more information.
'''

from   sidetrack import log
import smtplib
from   trinomial import anon

from .date_utils import human_datetime
from .settings import config


# Constants used throughout this file.
# .............................................................................

# Body of email message sent to users
_EMAIL = '''From: {sender}
To: {user}
Subject: {subject}

You started a digital loan through The University of Virginia Library at {start}.

  Title: {item.title}
  Author: {item.author}

  The loan period ends at {end} or when you click the "End Loan" button, whichever is first.
  Link to web viewer: {viewer}

Please note that UVA Library's digital loan service only functions in web browsers that support JavaScript. UVA Library's digital loan service is safe to use with JavaScript enabled in your browser and does not contain trackers or advertisements of any kind.

Information about loan policies can be found at {info_page}

We hope your experience with UVA Library's digital loan service is a pleasant one. Don't hesitate to send us feedback, and please report any problems. You can do it directly via email to {sender} or using our anonymous feedback form at {feedback}

Tell us how we did!  Please take the following survey related to your experience using the UVA Library eReserves System.
{survey_link}
'''


# Exported functions.
# .............................................................................

def send_email(user, item, start, end, base_url):
    try:
        # our SSO users are not email addresses as assumed here so we make a real email address
        email = f'{user}@virginia.edu'
        subject = f'Digital loan for "{item.title}"'
        viewer = f'https://search.lib.virginia.edu/sources/uva_library/items/{item.barcode}' #f'{base_url}/view/{item.barcode}'
        info_page = f'{base_url}/info'
        body = _EMAIL.format(item     = item,
                             start     = human_datetime(start),
                             end       = human_datetime(end),
                             viewer    = viewer,
                             info_page = info_page,
                             user      = email,
                             subject   = subject,
                             sender    = config('MAIL_SENDER'),
                             feedback  = 'https://search.lib.virginia.edu/feedback?url=https%3A%2F%2Freserves.library.virginia.edu',
                             survey_link = 'https://virginia.az1.qualtrics.com/jfe/form/SV_aaehed2qblw5owu')
        log(f'sending mail to {anon(email)} about loan of {item.barcode}')
        mailer  = smtplib.SMTP(config('MAIL_HOST'))
        mailer.sendmail(config('MAIL_SENDER'), [email], body)
    except Exception as ex:             # noqa PIE786
        log(f'unable to send mail: {str(ex)}')
