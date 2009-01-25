# -*- coding: utf-8 -*-
"""
Scheduler private data access layer

@author: Sébastien Renard (sebastien.renard@digitalfox.org)
@license:GNU GPL V3
"""

# Python imports

# Django imports
from django.db import models

# Chronix imports
from chronix.core.models import Task, Activity

LAUNCHED_TASK_STATES=(("FIRED", "Fired up"),
                      ("RUNNING", "Running"),
                      ("SUSPENDED", "Suspended"),
                      ("SUCCESS", "Finished successfully"),
                      ("FAILURE", "Finished with failure"))

TASK_SCHEDULER_STATES=(("RUNNING", "Currently running"),
                       ("SHUTTING DOWN", "Shutting down"),
                       ("STOPPED", "Stopped"),
                       ("SUSPENDED", "Suspended"),
                       ("KILLED", "Killed"))


class TaskSchedulerNode(models.Model):
    """A taskSchedulerNode is in charge of computing tasks workplan
    A set of task is affected to a taskScheduler. A task can be affected
    to more than one scheduler - it then will be planned by each one.
    One taskscheduler can feed one or more job scheduler"""
    name=models.CharField(max_length=200)
    tasks=models.ManyToManyField(Task, null=True, blank=True)
    start_date=models.DateTimeField(null=True, blank=True)
    state=models.CharField(max_length=20, choices=TASK_SCHEDULER_STATES)

    def __unicode__(self):
        return self.name

    def shutdown(self):
        """Shut down the task scheduler"""
        if self.state in ("RUNNING", "SUSPENDED"):
            self.state="SHUTTING DOWN"
            self.save()
        else:
            print "Cannot shutdown a task scheduler in state %s" % self.state

    def suspend(self):
        """Suspend the task scheduler"""
        if self.state=="RUNNING":
            self.state="SUSPENDED"
            self.save()
        else:
            print "Cannot suspend a task scheduler in state %s" % self.state

    def resume(self):
        """Resume the task scheduler"""
        if self.state in ("STOPPED", "KILLED", "SUSPENDED"):
            self.state="RUNNING"
            self.save()
        else:
            print "Cannot resume a task scheduler in state %s" % self.state

class LaunchedTask(models.Model):
    """A launched task represent a task that has been launched
    A task can have multiple launched task that represent distinct launched
    LaunchedTask instance are created from Task by the task scheduler"""
    planned_launch_date=models.DateTimeField(null=True, blank=True)
    real_launch_date=models.DateTimeField()
    update_date=models.DateTimeField(auto_now=True)
    current_activity=models.ForeignKey(Activity, related_name="current_chain_set", blank=True, null=True)
    state=models.CharField(max_length=20, choices=LAUNCHED_TASK_STATES)
    task=models.ForeignKey(Task)

class TaskEvent(models.Model):
    """A Task event is a communication message used to manage tasks
    A Task Event can be emited by:
        a task when starting or ending
        a call to the chronix CLI
        a call to the chronix API
        a call to the task event web service
    A task event is always received by a job scheduler
    An task event can be used to fire up unplanned tasks."""
    creation_date=models.DateTimeField(auto_now=True)
    done=models.BooleanField(default=False)
    targetTasks=models.ManyToManyField(Task, related_name="targetEvent") # Tasks targeted by the task event
    matchedTasks=models.ManyToManyField(Task, related_name="matchedEvent", null=True, blank=True) # Log of tasks that really receive the event
    #TODO; add parameter set that can overload task and task profile parameters

    def save(self):
        """Compute and cache the "done" state to save some time"""
        #TODO: task count is too weak. We should targetTask=matchedTask
        super(TaskEvent, self).save()
        if self.targetTasks.count()>0 and not self.done: # don't compute state if it is pointless
            if self.targetTasks.count()==self.matchedTasks.count():
                self.done=True # Cache result.
                super(TaskEvent, self).save()