#
# run the cron service (intended to be executed from a cron job)
#
# usage: manage.py cronjobs

from django.conf import settings
from django.core.management.base import NoArgsCommand
import django_cron

class Command(NoArgsCommand):
    help = "run the cron services (intended to be executed from a cron job)"

    def handle_noargs(self, **options):
        django_cron.autodiscover(start_timer=False, registering=False)
        print "cronjobs for %s finished" % settings.SITE_NAME
