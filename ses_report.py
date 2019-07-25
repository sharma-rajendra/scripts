"""
Standalone script to parse mail sending logs and alert people when some important mail
stops being sent.
"""

from __future__ import division
import os
import re
import csv
import json
import datetime
import subprocess
import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email import Encoders
MOVING_AVERAGE_DAYS = 30


def send_mail(subject, send_to, send_cc=[], message=None):
    COMMASPACE = ', '
    msg = MIMEText(message)
    msg['Subject'] = subject
    msg['From'] = "sender@example.com"
    msg['To'] = COMMASPACE.join(send_to)
    msg['CC'] = COMMASPACE.join(send_cc)

    send_tos = send_to + send_cc
    server = smtplib.SMTP('MAILSERVER_IP', 25)
    server.sendmail("sender@example.com", send_tos, msg.as_string())
    server.quit()


def smtp_report(path="/var/log/shine/postfix/", filename="mail.log-{date}.gz"):
    yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
    filename = filename.format(date=yesterday.strftime("%Y%m%d"))
    filename = os.path.join(path, filename)

    moving_avg_file = '/tmp/mail_moving_average.json'
    if not os.path.exists(moving_avg_file):
        with open(moving_avg_file, 'w') as f:
            json.dump({}, f)
    with open(moving_avg_file, 'r') as f:
        old_counts = json.load(f)

    command = (
        """zcat {filename} | awk '{{split($0,a,"X-MailerTag: "); print a[2]}}' """
        """| awk '{{split($0,a," from "); print a[1]}}' | sort | uniq -c | sort -nr """
    ).format(filename=filename)
    output = subprocess.check_output(
        command, stderr=subprocess.STDOUT, shell=True)
    normal_counts = []
    below_30_day_average = []
    normal_counts = ["Total: {}".format(output.strip().split('\n')[0].strip())]
    for line in output.strip().split('\n')[1:]:
        print line
        tag, count = reversed(line.strip().split(" "))
        count = int(count)
        try:
            tag_counts = old_counts[tag]
            tag_counts.append(count)
            tag_counts = tag_counts[-MOVING_AVERAGE_DAYS:]
            old_counts[tag] = tag_counts
        except KeyError:
            old_counts[tag] = [count]
        try:
            moving_average_count = sum(old_counts[tag]) / len(old_counts[tag])
        except ZeroDivisionError:
            moving_average_count = -1
        line = "{}: {}".format(tag, count)
        if count < 0.9 * moving_average_count:
            below_line = "{}: current: {}, average: {}".format(tag, count, moving_average_count)
            below_30_day_average.append(below_line)
        normal_counts.append(line)
    output = "\n".join(normal_counts)
    if below_30_day_average:
        output += '\n\nFollowing mails are below {} day average. Please investigate\n\n'.format(
            MOVING_AVERAGE_DAYS)
        output += "\n".join(below_30_day_average)
    print output
    with open(moving_avg_file, 'w') as f:
        old_counts = json.dump(old_counts, f)
    return output


def main():
    message = smtp_report()
    print "Sending Email started"
    send_mail(
        subject="SMTP reports",
        send_to=[
              "rajendrasharma@gmail.com"
        ],
        send_cc=[
            "raj@example.com"
        ],
        message=message,
    )
    print 'Mail Sent Successfully'


if __name__ == '__main__':
    main()

