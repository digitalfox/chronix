# -*- coding: utf-8 -*-
"""
Standard job queue algorithm shipped with Chronix

@author: Sébastien Renard (sebastien.renard@digitalfox.org)
@license:GNU GPL V3
"""

# Python imports
import random

# Chronix imports
from chronix.jobrunner.jobqueue import JobQueue

class FifoJobQueue(JobQueue):
    """A simple fifo job queue
    @todo: Make this class a plugin once plugin architecture defined"""
    def _get(self):
        return self.jobs.pop(0)

class RandomJobQueue(JobQueue):
    """A simple random job queue.
    @todo: Make this class a plugin once plugin architecture defined"""
    def _get(self):
        r=random.randint(0, len(self)-1)
        return self.jobs.pop(r)

class LifoJobQueue(JobQueue):
    """A simple lifo (last in first out) queue
    @todo: Make this class a plugin once plugin architecture defined"""
    def _get(self):
        return self.jobs.pop()

