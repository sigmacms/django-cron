try:
    from django.conf.urls.defaults import *
except:
    from django.conf.urls import *

urlpatterns = patterns('django_cron.admin_views',
    url(r'^restart/$', 'restart'),
)
