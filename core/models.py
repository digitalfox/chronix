# -*- coding: utf-8 -*-
"""
Core data access layer

@author: Sébastien Renard (sebastien.renard@digitalfox.org)
@license:GNU GPL V3
"""

# Djando imports
from django.db import models

# Python imports
import datetime # Needed to parse rrule attribute
from dateutil.rrule import rrule,YEARLY, MONTHLY, WEEKLY, DAILY, HOURLY, MINUTELY, SECONDLY 

FREQUENCIES=((YEARLY,   "Yearly"),
             (MONTHLY,  "Monthly"),
             (WEEKLY,   "Weekly"),
             (DAILY,    "Daily"),
             (HOURLY,   "Hourly"),
             (MINUTELY, "Minutely"),
             (SECONDLY, "Secondly"))

RRULES_KEYWORDS=("dtstart", "wkst", "count", "until", "bysetpos", "bymonth", "bymonthday",
                 "byyearday", "byweekno", "byweekday", "byhour", "byminute", "bysecond",
                 "byeaster")

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

class Recurrence(models.Model):
    """Define the recurrence of a task
    Simple recurrence for now (like a dateutil.rrule.rrule)
    More complex things could be done as midterm goal like rruleset (set of rules)"""
    name=models.CharField(max_length=200)
    frequency = models.IntegerField(max_length=20, choices=FREQUENCIES)
    params = models.TextField(null=True, blank=True)

    def get_rrule(self):
        """Create rrule object from its Recurrence representation
        @return: dateutil.rrule.rrule instance"""
        try:
            parDict=eval(self.params)
        except Exception, e:
            parDict={}
            print e
            #TODO: should we log an exception or break upstream ?
            # Bad data here means set_params is buggy or was not used to insert data
        if not isinstance(parDict, dict):
            #TODO: same question as above
            return {}
        return rrule(self.frequency, **parDict)

    def set_rrule(self, rule):
        """Set Recurrence according to rule
        @type rule: dateutil.rrule.rrule instance"""
        if not isinstance(rule, rrule):
            raise Exception("A dateutil.rrule.rrule object if requiered")
        self.frequency=rule._freq
        parDict={}
        for key in RRULES_KEYWORDS:
            parDict[key]=getattr(rule, "_"+key)
        self.params=repr(parDict) # Use str representation of the dict

class TaskProfile(models.Model):
    """A task profile define planification"""
    name=models.CharField(max_length=200)
    recurrence=models.ForeignKey(Recurrence, null=True)
    start_date=models.DateTimeField()
    end_date=models.DateTimeField()

class Task(models.Model):
    """A task represent the planification of a chain.
    A chain can have more than one task.
    A chain without task is not planned but can be launched by a specific event"""
    name=models.CharField(max_length=200)
    chain=models.ForeignKey(Chain)
    profile=models.ForeignKey(TaskProfile)

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
