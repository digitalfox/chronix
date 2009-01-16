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
    def __init__(self, name=None, node=None, daemonic=True):
        """Scheduler name or object (node) must be provided. If both are provided node object
        take precedence
        @param name: the task scheduler node name
        @type name: str or unicode
        @param taskSchedulerNode: the task scheduler node used to filter tasks
        @type taskSchedulerNode: TaskSchedulerNode
        @param daemonic: define if thread is daemon (ie not dying with main process end). Default it True
        """
        self.name=name
        self.taskSchedulerNode=node
        Thread.__init__(self)
        self.setDaemon(daemonic)

    def run(self):
        """Method executed when the thread object start() method is called"""
        if not self.taskSchedulerNode and self.name:
            try:
                self.taskSchedulerNode=TaskSchedulerNode.objects.get(name=self.name)
            except TaskSchedulerNode.DoesNotExist:
                print "No task scheduler with that name: %s" % self.name
                return
        elif not self.taskSchedulerNode and not self.name:
            print "You must either give the scheduler node name or object"
            return

        print "Starting scheduler node %s" % self.name
        self.taskSchedulerNode.state="RUNNING"
        self.taskSchedulerNode.save()
        self.loop()
        print "Scheduler node %s is stopped" % self.name


    def loop(self):
        """Main task scheduler loop.
        All enabled tasks are processed and launched if needed
        """
        while True:
            print "\nTask Scheduler %s (%s)" % (self.taskSchedulerNode.name, self.taskSchedulerNode.state)
            if self.taskSchedulerNode.state=="SHUTTING DOWN":
                self.taskSchedulerNode.state="STOPPED"
                self.taskSchedulerNode.save()
                break
            elif self.taskSchedulerNode.state=="SUSPENDED":
                sleep(SCHEDULE_INTERVAL)
                continue
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

    def shutdown(self):
        """Shut down the task scheduler"""
        self.taskSchedulerNode.state="SHUTTING DOWN"
        self.taskSchedulerNode.save()

    def suspend(self):
        """Suspend the task scheduler"""
        self.taskSchedulerNode.state="SUSPENDED"
        self.taskSchedulerNode.save()

    def resume(self):
        """Resume from suspend the task scheduler"""
        self.taskSchedulerNode.state="RUNNING"
        self.taskSchedulerNode.save()


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
        t=TaskSchedulerThread(name=sys.argv[1], daemonic=False)
        t.start()
        sleep(5)
        t.suspend()
        sleep(5)
        t.resume()
        sleep(5)
        t.shutdown()
    except IndexError:
        print "Task Scheduler name must be given in argument"
        sys.exit(1)

if __name__ == "__main__":
    main()
