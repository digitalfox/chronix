#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Chronix task scheduler

This module is in charge of processing task and feed the job queue

@author: Sébastien Renard (sebastien.renard@digitalfox.org)
@license:GNU GPL V3
"""

# Python imports
from time import sleep
import sys
from os.path import abspath, dirname, join, pardir
from datetime import datetime

## Setup django envt & django imports
sys.path.append(abspath(join(dirname(__file__), pardir)))
from django.core.management import setup_environ
import settings
setup_environ(settings)

# Django imports
from django.db import transaction

# Chronix imports
from chronix.scheduler.models import LaunchedTask, TaskSchedulerNode

SCHEDULE_INTERVAL=2 # In seconds

@transaction.commit_manually
def runTaskScheduler(taskSchedulerNode):
    """Main task scheduler loop.
    All enabled tasks are processed and launched if needed
    @param taskSchedulerNode: the task scheduler node used to filter tasks
    @type taskSchedulerNode: TaskSchedulerNode
    """
    #TODO: add a smart way to stop or suspend the loop
    while True:
        now=datetime.now()
        for task in taskSchedulerNode.tasks.filter(disable=False):
            print "\n***********\nProcessing task %s" % task.name
            try:
                processTask(task, now)
            except Exception, e:
                print "Got exception while processing task %s.\n%s" % (task.name, e)
        sleep(SCHEDULE_INTERVAL)

@transaction.commit_on_success
def processTask(task, refDate):
    """Process scheduling of a task. Launch it if needed.
    @param task: the task to process
    @type task: chronix.core.Task
    @param refDate: the date used to schedule. Usually it's now
    @type refDate: datetime.datetime
    """
    taskNeedSave=False
    taskNeedLaunch=False

    if task.profile.stop_if_last_run_failed and task.last_run_failed:
        print "Don't run this task because last run failed"
        return

    if not task.next_run and task.isPlanned():
        task.computeNextRun(refDate)
        taskNeedSave=True

    for event in task.targetEvent.filter(done=False):
        if task in event.matchedTasks.all():
            # This event is not for us, skipping
            # It is still not mark done because another tasks wait it
            continue
        print "task receive event"
        event.matchedTasks.add(task)
        event.save()
        taskNeedLaunch=True

    if task.next_run and task.next_run < refDate:
        taskNeedLaunch=True

    if taskNeedLaunch:
        print "Launch task %s" % task.name
        launchTask(task, refDate)
        # Update task for its next run
        task.last_run=task.next_run
        task.computeNextRun(refDate)
        taskNeedSave=True

    if taskNeedSave:
        task.save()

def launchTask(task, refDate):
    """Launch a task by creating a LaunchedTask
    @param task: task used to create the launchedTask. Task object is not modified.
    @type task: chronix.core.Task
    @param refDate: the date used to log real launch date.
    @type refDate: datetime.datetime"""
    # Create the launched task
    launchedTask=LaunchedTask()
    launchedTask.task=task # Reference task
    launchedTask.state="FIRED"
    launchedTask.planned_launch_date=task.next_run
    launchedTask.real_launch_date=refDate
    launchedTask.save()

def main():
    #TODO: handle that properly in conf.
    # For now, taskScheduler naem is receive as argv[1]
    try:
        taskSchedulerNode=TaskSchedulerNode.objects.get(name=sys.argv[1])
        runTaskScheduler(taskSchedulerNode)
    except TaskSchedulerNode.DoesNotExist:
        print "This task scheduler does not exist."
        sys.exit(1)
    except IndexError:
        print "Task Scheduler name must be given in argument"
        sys.exit(1)

if __name__ == "__main__":
    main()
