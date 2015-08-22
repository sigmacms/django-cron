try:
    from django.conf.urls.defaults import url, patterns
except ImportError:
    from django.conf.urls import url, patterns

urlpatterns = patterns(
    'django_cron.admin_views',
    url(r'^restart/$', 'restart'),
)
