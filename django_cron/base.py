"""
Copyright (c) 2007-2008, Dj Gilcrease
All rights reserved.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

import os
import cPickle
from threading import Timer
from datetime import datetime
from datetime import timedelta
import sys
import socket

from django.template.loader import render_to_string
from django.dispatch import dispatcher
from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import mail_admins
from signals import cron_done
import models
import cron_settings

HOUR = 60
DAY = HOUR*24
WEEK = DAY*7
MONTH = int(WEEK*4.333) # well sorta

# how often to check if jobs are ready to be run (in seconds)
# in reality if you have a multithreaded server, it may get checked
# more often that this number suggests, so keep an eye on it...
# default value: 300 seconds == 5 min
polling_frequency = getattr(settings, "CRON_POLLING_FREQUENCY", 300)

cron_pid_file = cron_settings.PID_FILE

class Job(object):
    run_every = DAY

    def run(self, *args, **kwargs):  
        self.job()
        cron_done.send(sender=self, *args, **kwargs)
        
    def job(self):
        """
        Should be overridden (this way is cleaner, but the old way - overriding run() - will still work)
        """
        pass

class CronScheduler(object):
    def register(self, job_class, *args, **kwargs):
        """
        Register the given Job with the scheduler class
        """
        
        job_instance = job_class()
        
        if not isinstance(job_instance, Job):
            raise TypeError("You can only register a Job not a %r" % job_class)

        job, created = models.Job.objects.get_or_create(name=str(job_instance.__class__))
        if created:
            job.instance = cPickle.dumps(job_instance)
        job.args = cPickle.dumps(args)
        job.kwargs = cPickle.dumps(kwargs)
        job.run_frequency = job_instance.run_every
        job.save()


    def unregister(self, job_class, *args, **kwargs):

        job_instance = job_class()
        if not isinstance(job_instance, Job):
            raise TypeError("You can only unregister a Job not a %r" % job_class)
        try:
            job = models.Job.objects.get(name=str(job_instance.__class__))
            job.delete()
        except models.Job.DoesNotExist:
            pass


    def execute(self, start_timer=True, registering=False):
        """
        Queue all Jobs for execution
        """
        if not registering:
            status, created = models.Cron.objects.get_or_create(pk=1)

            ###PID code
            if cron_pid_file:
                if not os.path.exists(cron_pid_file):
                    f = open(cron_pid_file, 'w') #create the file if it doesn't exist yet.
                    f.close()

            # This is important for 2 reasons:
            #     1. It keeps us for running more than one instance of the
            #        same job at a time
            #     2. It reduces the number of polling threads because they
            #        get killed off if they happen to check while another
            #        one is already executing a job (only occurs with
            #         multi-threaded servers)

            if status.executing:
                print "Already executing"
                ###PID code
                ###check if django_cron is stuck
                if cron_pid_file:
                    pid_file = open(cron_pid_file, 'r')
                    pid_content = pid_file.read()
                    pid_file.close()
                    if not pid_content:
                        pass#File is empty, do nothing
                    else:
                        pid = int(pid_content)
                        if os.path.exists('/proc/%s' % pid):
                            print 'Verified! Process with pid %s is running.' % pid
                        else:
                            print 'Oops! process with pid %s is not running.' % pid
                            print 'Fixing status in db. '
                            status.executing = False
                            status.save()
                            subject = 'Fixed cron job for %s' % settings.SITE_NAME
                            context = {
                                'pid': pid,
                                'host': socket.gethostname(),
                                'settings': settings,
                                'non_queued_jobs': models.Job.objects.filter(queued=False),
                                'queued_jobs': models.Job.objects.exclude(queued=False),
                            }
                            body = render_to_string('django_cron/fixed_job_stuck.txt', context)
                            mail_admins(subject, body, fail_silently=True)
                return

            status.executing = True
            ###PID code
            if cron_pid_file:
                pid_file = open(cron_pid_file, 'w')
                pid_file.write(str(os.getpid()))
                pid_file.close()
            try:
                status.save()
            except:
                # this will fail if you're debugging, so we want it
                # to fail silently and start the timer again so we
                # can pick up where we left off once debugging is done
                if start_timer:
                    # Set up for this function to run again
                    Timer(polling_frequency, self.execute).start()
                return

            jobs = models.Job.objects.all()
            for job in jobs:
                if job.queued:
                    
                    # Discard the seconds to prevent drift. Thanks to Josh Cartmell
                    now = datetime.now()
                    now = datetime(now.year, now.month, now.day, now.hour, now.minute)
                    last_run = datetime(job.last_run.year, job.last_run.month, job.last_run.day, job.last_run.hour, job.last_run.minute)
                    
                    if (now - last_run) >= timedelta(minutes=job.run_frequency):
                        inst = cPickle.loads(str(job.instance))
                        args = cPickle.loads(str(job.args))
                        kwargs = cPickle.loads(str(job.kwargs))

                        try:
                            inst.run(*args, **kwargs)
                            job.last_run = datetime.now()
                            job.save()

                        except Exception, err:
                            # if the job throws an error, just remove it from
                            # the queue. That way we can find/fix the error and
                            # requeue the job manually
                            try:
                                for u in User.objects.filter(is_staff=True):
                                    u.message_set.create(message="Error running job: %s: %s Please notify the administrator." % (job.name, err))
                            except:
                                #Code will fail in django 1.4 or later as user.message_set is no longer available
                                pass
                            job.queued = False
                            job.save()
                            import traceback
                            exc_info = sys.exc_info()
                            stack = ''.join(traceback.format_tb(exc_info[2]))
                            if not settings.LOCAL_DEV:
                                self.mail_exception(job.name, inst.__module__, err, stack)
                            else:
                                print stack
            status.executing = False
            status.save()

        if start_timer:
            # Set up for this function to run again
            Timer(polling_frequency, self.execute).start()


    def mail_exception(self, job, module, err, stack=None):
        subject = 'Cron job failed for %s' % settings.SITE_NAME
        body = '''
        Cron job failed for %s
        Job: %s
        Module: %s
        Error message: %s
        Time: %s
        
        Stack Trace: %s
        ''' % (settings.SITE_NAME, job, module, str(err), datetime.now().strftime("%d %b %Y"), ''.join(stack))
        
        mail_admins(subject, body, fail_silently=True)


cronScheduler = CronScheduler()

