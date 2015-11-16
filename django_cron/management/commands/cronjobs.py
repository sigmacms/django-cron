"""
Run the cron service (intended to be executed from a cron job)

Rsage: manage.py cronjobs
"""

import sys
import signal
from datetime import datetime
import logging
logger = logging.getLogger('django.django_cron')

from django.conf import settings
from django.core.management.base import NoArgsCommand
import django_cron
from django_cron import cron_settings


def log_warning(warning):
    logger.log(cron_settings.LOG_LEVEL_FOR_STUCK_CRON, warning)


# Exit when the command last longer than TIMEOUT
if cron_settings.TIMEOUT:
    def timeout_check(signum, stack):
        log_warning('django_cron has timeout. exiting. ')
        print 'django_cron has timeout. exiting. '
        sys.exit()
    
    signal.signal(signal.SIGALRM, timeout_check)
    signal.alarm(cron_settings.TIMEOUT)



# Warn when the command last longer than WARN_ON_STUCK_CRON
if cron_settings.WARN_ON_STUCK_CRON:
    def warn_on_stuck_cron(signum, stack):
        log_warning('django_cron is stuck for more than {} hours.'.format(cron_settings.WARN_ON_STUCK_CRON/3600))

    signal.signal(signal.SIGALRM, warn_on_stuck_cron)
    signal.alarm(cron_settings.WARN_ON_STUCK_CRON)


class Command(NoArgsCommand):
    help = "run the cron services (intended to be executed from a cron job)"

    def handle_noargs(self, **options):
        django_cron.autodiscover(start_timer=False, registering=False)
        print "%s: Cronjobs for %s finished" % (datetime.now(), settings.SITE_NAME)
