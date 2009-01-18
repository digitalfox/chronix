from django.conf.urls.defaults import *

from django.contrib import admin
admin.autodiscover()

# Django rest API
from django_restapi.model_resource import Collection
from django_restapi.responder import JSONResponder
from django_restapi.receiver import JSONReceiver
from chronix.scheduler.models import Event

event_resource = Collection(
    queryset = Event.objects.all(),
    permitted_methods = ('GET', 'POST', 'PUT', 'DELETE'),
    #expose_fields = ('id', 'targetTasks'),
    responder = JSONResponder(),
    receiver = JSONReceiver(),
)

urlpatterns = patterns('',
    # Example:
    # (r'^chronix/', include('chronix.foo.urls')),

    (r'^admin/(.*)', admin.site.root),
    url(r'^json/event/(.*?)/?$', event_resource),
)
