import os
import logging
from django.conf import settings


base_dir = getattr(settings, 'BASE_DIR', '') or getattr(settings, 'PROJECT_DIR', '')
PID_FILE = getattr(settings, 'CRON_PID_FILE', os.path.join(base_dir, 'cron_pid.pid'))
RETRY = getattr(settings, 'CRON_RETRY', False)
TIMEOUT = getattr(settings, 'CRON_TIMEOUT', False)
WARN_ON_STUCK_CRON = getattr(settings, 'CRON_WARN_ON_STUCK_CRON', 12 * 3600) # a warning when cron is stuck for 12hrs
LOG_LEVEL_FOR_STUCK_CRON = getattr(settings, 'CRON_LOG_LEVEL_FOR_STUCK_CRON', logging.CRITICAL)
