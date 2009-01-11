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

class TaskSchedulerNode(models.Model):
    """A taskSchedulerNode is in charge of computing tasks workplan
    A set of task is affected to a taskScheduler. A task can be affected
    to more than one scheduler - it then will be planned by each one.
    One taskscheduler can feed one or more job scheduler"""
    name=models.CharField(max_length=200)
    tasks=models.ManyToManyField(Task)
    running=models.BooleanField(default=False)
    start_date=models.DateTimeField(null=True, blank=True)

    def __unicode__(self):
        return self.name

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

class Event(models.Model):
    """An event is a communication message
    An event can be emited by:
        a task when starting or ending
        a call to the event CLI
        a call to the event API
        a call to the event web service
    An event is always received by a job scheduler
    An event can be used to fire up tasks."""
    creation_date=models.DateTimeField()
    done_date=models.DateTimeField()
    task=models.ManyToManyField(Task) # The targeted task
    done=models.BooleanField(default=False) # Do we need more that two state ?