import os

from django.conf import settings

PID_FILE = getattr(settings, 'CRON_PID_FILE', os.path.join(settings.PROJECT_DIR, 'cron_pid.pid'))
RETRY = getattr(settings, 'CRON_RETRY', False)
