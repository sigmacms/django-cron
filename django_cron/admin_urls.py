from django.conf.urls.defaults import *

urlpatterns = patterns('django_cron.admin_views',
    url(r'^restart/$', 'restart'),
)
