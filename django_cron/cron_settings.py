import os

from django.conf import settings

base_dir = getattr(settings, 'BASE_DIR', '') or getattr(settings, 'PROJECT_DIR', '')
PID_FILE = getattr(settings, 'CRON_PID_FILE', os.path.join(base_dir, 'cron_pid.pid'))
RETRY = getattr(settings, 'CRON_RETRY', False)
