# -*- coding: utf-8 -*-
"""
Chronix core admin interface definition

The admin interface is mostly intended for test and dev purpose.
For a real web user interface to Chronix, look at the console or
repository application

@author: Sébastien Renard (sebastien.renard@digitalfox.org)
@license:GNU GPL V3
"""

from django.contrib import admin

from chronix.core.models import Activity, ShellActivity, \
                                Application, Chain, \
                                Condition, TimeCondition, FlowCondition, \
                                Task, TaskProfile, Recurrence

admin.site.register(Activity)
admin.site.register(ShellActivity)

admin.site.register(Application)
admin.site.register(Chain)

admin.site.register(Condition)
admin.site.register(TimeCondition)
admin.site.register(FlowCondition)

admin.site.register(Task)
admin.site.register(TaskProfile)
admin.site.register(Recurrence)