# -*- coding: utf-8 -*-
"""
Chronix Job Runner admin interface definition

The admin interface is mostly intended for test and dev purpose.

@author: Sébastien Renard (sebastien.renard@digitalfox.org)
@license:GNU GPL V3
"""

from django.contrib import admin

from chronix.jobrunner.models import JobRunnerNode, JobQueueConfig, JobQueueAlgorithm

admin.site.register(JobRunnerNode)
admin.site.register(JobQueueConfig)
admin.site.register(JobQueueAlgorithm)
