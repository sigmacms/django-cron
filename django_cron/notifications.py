######################################################################
# For use with https://github.com/andybak/django-admin-notifications #
######################################################################

from datetime import datetime
from datetime import timedelta

from django.utils.html import escape

import admin_notifications

from models import Job

def delta_display(delta):
    s = ''
    if delta.days:
        s += '%s days ' % delta.days
    s += '%s minutes' % str(delta.seconds/60)
    return s

def notification():
    msgs = []
    jobs = Job.objects.all()
    for job in jobs:
        msg = ""
        miss = datetime.now() - job.last_run
        has_missed = (miss - timedelta(seconds=job.run_frequency*60)) > timedelta(seconds=3*60) # If a job is late by at least the cron interval+fudge factor
        if not(job.queued):
            msg += "Job: %s isn't currently queued. " % escape(job.name)
        if has_missed:
            msg += "Job: %s  has missed it's schedule by %s" % (escape(job.name), delta_display(miss))
            if job.queued:
                msg += " but has been re-scheduled."
            else:
                msg += "<br />Click here to <a href='/admin/cron/restart/'>re-queue all jobs</a>"
        if msg:
            msgs.append(msg)
    if msgs:
        return "<br />".join(msgs)

admin_notifications.register(notification)