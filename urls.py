from django.conf.urls.defaults import *

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    # (r'^chronix/', include('chronix.foo.urls')),

    (r'^admin/(.*)', admin.site.root),
)
