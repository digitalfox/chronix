# -*- coding: utf-8 -*-
"""
Chronix scheduler admin interface definition

The admin interface is mostly intended for test and dev purpose.
For a real web user interface to Chronix, look at the console or
repository application

@author: Sébastien Renard (sebastien.renard@digitalfox.org)
@license:GNU GPL V3
"""

from django.contrib import admin

from chronix.scheduler.models import TaskEvent, LaunchedTask, TaskSchedulerNode

admin.site.register(TaskEvent)
admin.site.register(LaunchedTask)
admin.site.register(TaskSchedulerNode)