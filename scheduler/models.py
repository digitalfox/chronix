# -*- coding: utf-8 -*-
"""
Scheduler private data access layer

@author: Sébastien Renard (sebastien.renard@digitalfox.org)
@license:GNU GPL V3
"""

from django.db import models

# Chronix imports
from chronix.core.models import Task, Activity

LAUNCHED_TASK_STATES=(("FIRED", "Fired up"),
                      ("RUNNING", "Running"),
                      ("SUSPENDED", "Suspended"),
                      ("SUCCESS", "Finished successfully"),
                      ("FAILURE", "Finished with failure"))

class LaunchedTask(models.Model):
    """A launched task represent a task that has been launched
    A task can have multiple launched task that represent distinct launched
    LaunchedTask instance are created from Task by the task scheduler"""
    planned_launch_date=models.DateTimeField()
    real_launch_date=models.DateTimeField()
    update_date=models.DateTimeField(auto_now=True)
    current_activity=models.ForeignKey(Activity, related_name="current_chain_set", blank=True, null=True)
    state=models.CharField(max_length=20, choices=LAUNCHED_TASK_STATES)
    task=models.ForeignKey(Task)
