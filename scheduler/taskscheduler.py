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

# Chronix imports
from chronix.core.models import Task

SCHEDULE_INTERVAL=1 # In seconds

def processTasks():
    while True:
        now=datetime.now()
        for task in Task.objects.filter(disable=False):
            taskNeedSave=False
            print "processing task %s" % task.name
            if task.profile.stop_if_last_run_failed and task.last_run_failed:
                print "Don't run this task because last run failed"
                break
            if not task.next_run and task.isPlanned():
                task.computeNextRun()
                taskNeedSave=True
            if task.next_run and task.next_run < now:
                print "Should run !"
                task.last_run=task.next_run
                task.computeNextRun()
                taskNeedSave=True
            if taskNeedSave:
                task.save()
        sleep(SCHEDULE_INTERVAL)

def main():
    processTasks()

if __name__ == "__main__":
    main()
