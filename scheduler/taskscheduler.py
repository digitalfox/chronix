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
from threading import Thread

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

class TaskSchedulerThread(Thread):
    """A thread running a task scheduler node"""
    def __init__(self, name=None, node=None, cleanup=False):
        """Scheduler name or object (node) must be provided. If both are provided node object
        take precedence
        @param name: the task scheduler node name
        @type name: str or unicode
        @param taskSchedulerNode: the task scheduler node used to filter tasks
        @type taskSchedulerNode: TaskSchedulerNode
        @param cleanup: Force state cleanup to recover from dirty state
        @type cleanup: Bool
        """
        self.taskSchedulerNode=node

        if not node and name:
            try:
                self.taskSchedulerNode=TaskSchedulerNode.objects.get(name=self.name)
            except TaskSchedulerNode.DoesNotExist:
                print "No task scheduler with that name: %s" % self.name
                return
        elif not node and not self.name:
            print "You must either give the scheduler node name or object"
            return

        if cleanup:
            if self.taskSchedulerNode.state=="STOPPED":
                print "Cleaning state not required, task scheduler was stopped properly"
            else:
                print "Cleaning up task scheduler state from %s to KILLED" % self.taskSchedulerNode.state
                self.taskSchedulerNode.state="KILLED"
                self.taskSchedulerNode.save()

        Thread.__init__(self)

    def run(self):
        """Method executed when the thread object start() method is called"""
        if self.taskSchedulerNode.state=="RUNNING":
            print "Task scheduler seems to be already running according to database state"
            print "Cannot start a second one"
            return

        if self.taskSchedulerNode.state=="KILLED":
            print "Task scheduler was killed. Performing cleaning operation."
            # Nothing to do for now.

        if self.taskSchedulerNode.state=="SHUTTING DOWN":
            print "Task scheduler seems shutting down according to database state"
            print "Cannot task a second one"
            return

        print "Starting scheduler node %s" % self.taskSchedulerNode.name
        self.taskSchedulerNode.start_date=datetime.now()
        self.taskSchedulerNode.resume()
        self.loop()
        print "Scheduler node %s is stopped" % self.taskSchedulerNode.name


    def loop(self):
        """Main task scheduler loop.
        All enabled tasks are processed and launched if needed
        """
        while True:
            print "\nTask Scheduler %s (%s)" % (self.taskSchedulerNode.name, self.taskSchedulerNode.state)
            if self.taskSchedulerNode.state=="SHUTTING DOWN":
                self.taskSchedulerNode.state="STOPPED"
                self.taskSchedulerNode.save()
                break # Exiting loop
            elif self.taskSchedulerNode.state=="SUSPENDED":
                sleep(SCHEDULE_INTERVAL)
                continue # Do nothing
            elif self.taskSchedulerNode.state in ("KILLED", "STOPPED"):
                print "This node should not run with such state %s" % self.taskSchedulerNode.state
                break
            else:
                now=datetime.now()
                for task in self.taskSchedulerNode.tasks.filter(disable=False):
                    print "***********\nProcessing task %s" % task.name
                    try:
                        processTask(task, now)
                    except Exception, e:
                        print "Got exception while processing task %s.\n%s" % (task.name, e)
                sleep(SCHEDULE_INTERVAL)


@transaction.commit_on_success
def processTask(task, refDate):
    """Process scheduling of a task. Launch it if needed.
    @note: This function use transaction.commit_on_success
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
    # For now, taskScheduler name is receive as argv[1]

    try:
        # test sequence
        node=TaskSchedulerNode.objects.get(name=sys.argv[1])
        t=TaskSchedulerThread(node=node, cleanup=True)
        t.setDaemon(False) # Ease debug
        t.start()
        sleep(5)
        node.suspend()
        sleep(5)
        node.resume()
        sleep(5)
        node.shutdown()
    except IndexError:
        print "Task Scheduler name must be given in argument"
        sys.exit(1)
    except TaskSchedulerNode.DoesNotExist:
        print "No Task scheduler with such name"
        print "Task scheduler availables: %s" % ", ".join([unicode(t) for t in TaskSchedulerNode.objects.all()])
        sys.exit(1)

if __name__ == "__main__":
    main()
