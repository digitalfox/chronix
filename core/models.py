# -*- coding: utf-8 -*-
"""
Core data access layer

@author: Sébastien Renard (sebastien.renard@digitalfox.org)
@license:GNU GPL V3
"""

from django.db import models

# Create your models here.

class Application(models.Model):
    """A consistent set of chain and tasks that represent the
    workplan of an application"""
    name=models.CharField(max_length=50)

class Chain(models.Model):
    """A succession of activities with defined conditions."""
    name=models.CharField(max_length=200)
    application=models.ForeignKey(Application)

class Condition(models.Model):
    """A condition is a rule to start the next activity in a chain."""
    pass

class TimeCondition(Condition):
    """A condition based on time"""
    pass

class FlowCondition(Condition):
    """A condition based on activity success, failure"""
    pass

class ExclusionCondition(Condition):
    """A condition used  to prevent concurent running of some activities"""
    pass

class Activity(models.Model):
    """The most unitary peace of work.
    An activity define parameters needed to launch properly a job (see below)."""
    name=models.CharField(max_length=200)
    chain=models.ForeignKey(Chain)
    startingConditions=models.ManyToManyField(Condition)

class ShellActivity(Activity):
    """An activity launched via the system shell"""
    # Env varchar should be changed into a list of env variable structured in groups
    env=models.CharField(max_length=2000)
    command_line=models.CharField(max_length=2000) # Should be more elaborated (split command and arguments)

class WebServiceActivity(Activity):
    """A web service activity. Common parts between REST and W3C Web services"""
    url=models.CharField(max_length=2000)

class StoredProcedureActivity(Activity):
    """A rdbms store procedure"""
    procedure_name=models.CharField(max_length=2000)
    connection_string=models.CharField(max_length=200)

class Task(models.Model):
    """A task represent the planification of a chain.
    A chain can have more than one task.
    A chain without task is not planned but can be launched by a specific event"""
    chain=models.ForeignKey(Chain)
    profile=models.CharField(max_length=200)

class Event(models.Model):
    """An event is a communication message
    An event can be emited by:
        a task when starting or ending
        a call to the event CLI
        a call to the event API
        a call to the event web service
    An event is always received by a job scheduler
    An event can be used to fire up a task."""
    creation_date=models.DateField()
    done_date=models.DateField()
    task=models.ForeignKey(Task) # The targeted task
    done=models.BooleanField(default=False) # Do we need more that two state ?
