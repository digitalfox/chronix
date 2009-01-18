#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file has been automatically generated, changes may be lost if you
# go and generate it again. It was generated with the following command:
# ./manage.py dumpscript core scheduler

import datetime
from decimal import Decimal
from django.contrib.contenttypes.models import ContentType

def run():
    from chronix.core.models import Application

    core_application_1 = Application()
    core_application_1.name = u'test application'
    core_application_1.save()

    from chronix.core.models import Condition


    from chronix.core.models import TimeCondition


    from chronix.core.models import FlowCondition


    from chronix.core.models import ExclusionCondition


    from chronix.core.models import OrCondition


    from chronix.core.models import Activity

    core_activity_1 = Activity()
    core_activity_1.name = u'begin activity'
    core_activity_1.save()

    core_activity_2 = Activity()
    core_activity_2.name = u'end activity'
    core_activity_2.save()

    from chronix.core.models import ShellActivity


    from chronix.core.models import WebServiceActivity


    from chronix.core.models import StoredProcedureActivity


    from chronix.core.models import Chain

    core_chain_1 = Chain()
    core_chain_1.name = u'test chain'
    core_chain_1.application = core_application_1
    core_chain_1.start_activity = core_activity_1
    core_chain_1.end_activity = core_activity_2
    core_chain_1.save()

    from chronix.core.models import Recurrence

    core_recurrence_1 = Recurrence()
    core_recurrence_1.name = u'every 10 sec'
    core_recurrence_1.frequency = 6
    core_recurrence_1.start_date = datetime.datetime(2009, 1, 18, 20, 11, 17)
    core_recurrence_1.params = u'{"interval":10}'
    core_recurrence_1.save()

    from chronix.core.models import TaskProfile

    core_taskprofile_1 = TaskProfile()
    core_taskprofile_1.name = u'test profile'
    core_taskprofile_1.recurrence = core_recurrence_1
    core_taskprofile_1.stop_if_last_run_failed = True
    core_taskprofile_1.forgot_misfire = True
    core_taskprofile_1.save()

    from chronix.core.models import Task

    core_task_1 = Task()
    core_task_1.name = u'test task'
    core_task_1.chain = core_chain_1
    core_task_1.profile = core_taskprofile_1
    core_task_1.disable = False
    core_task_1.next_run = datetime.datetime(2009, 1, 18, 20, 12, 47)
    core_task_1.last_run = datetime.datetime(2009, 1, 18, 20, 12, 37)
    core_task_1.last_run_failed = False
    core_task_1.save()

    from chronix.scheduler.models import TaskSchedulerNode

    scheduler_taskschedulernode_1 = TaskSchedulerNode()
    scheduler_taskschedulernode_1.name = u'test'
    scheduler_taskschedulernode_1.start_date = datetime.datetime(2009, 1, 18, 20, 12, 30, 685226)
    scheduler_taskschedulernode_1.state = u'STOPPED'
    scheduler_taskschedulernode_1.save()

    scheduler_taskschedulernode_1.tasks.add(core_task_1)

    from chronix.scheduler.models import LaunchedTask

    scheduler_launchedtask_1 = LaunchedTask()
    scheduler_launchedtask_1.planned_launch_date = datetime.datetime(2009, 1, 18, 20, 12, 37)
    scheduler_launchedtask_1.real_launch_date = datetime.datetime(2009, 1, 18, 20, 12, 40, 705656)
    scheduler_launchedtask_1.update_date = datetime.datetime(2009, 1, 18, 20, 12, 40, 708405)
    scheduler_launchedtask_1.current_activity = None
    scheduler_launchedtask_1.state = u'FIRED'
    scheduler_launchedtask_1.task = core_task_1
    scheduler_launchedtask_1.save()

    from chronix.scheduler.models import Event


