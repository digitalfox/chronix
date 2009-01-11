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

RRULES_KEYWORDS=("wkst", "count", "until", "bysetpos", "bymonth", "bymonthday",
                 "byyearday", "byweekno", "byweekday", "byhour", "byminute", "bysecond",
                 "byeaster")

class Application(models.Model):
    """A consistent set of chain and tasks that represent the
    workplan of an application"""
    name=models.CharField(max_length=50)

    def __unicode__(self):
        return self.name

class Condition(models.Model):
    """A condition is a rule to start the next activity in a chain."""
    pass

class TimeCondition(Condition):
    """A condition based on time"""
    min_time=models.TimeField(blank=True)
    max_time=models.TimeField(blank=True)

    def __unicode__(self):
        if self.min_time and self.max_time:
            return u"%s < x < %s" % (self.min_time, self.max_time)
        elif self.min_time:
            return u"%s < x" % self.min_time
        elif self.max_time:
            return u"x < %s" % self.max_time
        else:
            return "Undefined"

    def isTrue(self, refTime=None):
        """
        @param refTime: Use time to resolve condition. Default is now()
        @type date: datetime.time
        @return: bool"""
        result=True
        refTime=refTime or datetime.datetime.now().time()
        if self.min_time:
            result=result and (self.min_time < refTime)
        if self.max_time:
            result=result and (self.max_time > refTime)
        return result

class FlowCondition(Condition):
    """A condition based on activity success, failure"""
    pass

class ExclusionCondition(Condition):
    """A condition used  to prevent concurent running of some activities"""
    pass

class OrCondition(Condition):
    """A condition that is true if any of its sub condition is True"""
    subConditions=models.ManyToManyField(Condition, related_name="orSubConditions")

    def isTrue(self):
        result=True
        for condition in self.subConditions:
            result=result and condition.isTrue()
        return result

class Activity(models.Model):
    """The most unitary peace of work.
    An activity define parameters needed to launch properly a job (see below)."""
    name=models.CharField(max_length=200)
    startingConditions=models.ManyToManyField(Condition, blank=True)

    def __unicode__(self):
        return self.name

class ShellActivity(Activity):
    """An activity launched via the system shell"""
    # Env varchar should be changed into a list of env variable structured in groups
    env=models.CharField(max_length=2000, blank=True)
    command_line=models.CharField(max_length=2000) # Should be more elaborated (split command and arguments)

class WebServiceActivity(Activity):
    """A web service activity. Common parts between REST and W3C Web services"""
    url=models.CharField(max_length=2000)

class StoredProcedureActivity(Activity):
    """A rdbms store procedure"""
    procedure_name=models.CharField(max_length=2000)
    connection_string=models.CharField(max_length=200)

class Chain(models.Model):
    """A succession of activities with defined conditions."""
    name=models.CharField(max_length=200)
    application=models.ForeignKey(Application)
    start_activity=models.ForeignKey(Activity, related_name="starting_chain_set")
    end_activity=models.ForeignKey(Activity, related_name="ending_chain_set")

    def __unicode__(self):
        return self.name

class Recurrence(models.Model):
    """Define the recurrence of a task
    Simple recurrence for now (like a dateutil.rrule.rrule)
    More complex things could be done as midterm goal like rruleset (set of rules)"""
    name=models.CharField(max_length=200)
    frequency = models.IntegerField(max_length=20, choices=FREQUENCIES)
    start_date=models.DateTimeField()
    params = models.TextField(null=True, blank=True)

    def __unicode__(self):
        return "%s (%s)" % (self.name, self.get_frequency_display())

    def get_rrule(self):
        """Create rrule object from its Recurrence representation
        @return: dateutil.rrule.rrule instance"""
        parDict={}
        try:
            if self.params:
                parDict=eval(self.params)
        except Exception, e:
            print "Bad recurrence parameter: %s" % e
            #TODO: should we log an exception or break upstream ?
            # Bad data here means set_params is buggy or was not used to insert data
        parDict["cache"]=True # Allow rrule cache to optimise multiple access to same rrule
        parDict["dtstart"]=self.start_date
        return rrule(self.frequency, **parDict)

    def set_rrule(self, rule):
        """Set Recurrence according to rule
        @type rule: dateutil.rrule.rrule instance"""
        if not isinstance(rule, rrule):
            raise Exception("A dateutil.rrule.rrule object if requiered")
        self.frequency=rule._freq
        self.start_date=rule._dtstart
        parDict={}
        for key in RRULES_KEYWORDS:
            parDict[key]=getattr(rule, "_"+key)
        self.params=repr(parDict) # Use str representation of the dict

class TaskProfile(models.Model):
    """A task profile define sets of reccurence and parameters"""
    name=models.CharField(max_length=200)
    recurrence=models.ForeignKey(Recurrence, blank=True, null=True)
    stop_if_last_run_failed=models.BooleanField(default=True)
    #TODO: add a parameter that make a task forget old runs and only react to future occurences

    #TODO: define here parameters set for task profile

class Task(models.Model):
    """A task represent the planification of a chain.
    A chain can have more than one task.
    A chain without task is not planned but can be launched by a specific event"""
    name=models.CharField(max_length=200)
    chain=models.ForeignKey(Chain)
    profile=models.ForeignKey(TaskProfile)
    disable=models.BooleanField(default=False)
    next_run=models.DateTimeField(blank=True, null=True)
    last_run=models.DateTimeField(blank=True, null=True)
    last_run_failed=models.BooleanField(default=False)

    def __unicode__(self):
        return self.name

    def computeNextRun(self):
        """Compute the next date to run this task and store it in next_run field"""
        if self.profile.recurrence is None:
            self.next_run=None
            return
        if self.last_run:
            dateRef=self.last_run
        else:
            # Never run, use now as reference for next run
            print "no last run date, using now as reference"
            dateRef=datetime.datetime.now()
        self.next_run=self.profile.recurrence.get_rrule().after(dateRef)
        print "next run: %s" % self.next_run

    def isPlanned(self):
        """Check if task is planned"""
        if self.profile.recurrence:
            return True
        else:
            return False 

class Event(models.Model):
    """An event is a communication message
    An event can be emited by:
        a task when starting or ending
        a call to the event CLI
        a call to the event API
        a call to the event web service
    An event is always received by a job scheduler
    An event can be used to fire up a task."""
    creation_date=models.DateTimeField()
    done_date=models.DateTimeField()
    task=models.ForeignKey(Task) # The targeted task
    done=models.BooleanField(default=False) # Do we need more that two state ?
