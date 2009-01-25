# -*- coding: utf-8 -*-
"""
Jobrunner configuration data access layer

@author: Sébastien Renard (sebastien.renard@digitalfox.org)
@license:GNU GPL V3
"""

# Python imports

# Django imports
from django.db import models


class JobRunnerNode(models.Model):
    """Job runner node configuration"""
    name=models.CharField(max_length=200)
    max_runner=models.IntegerField() # Max runner for this node

class JobQueueConfig(models.Model):
    """Generic job queue configuration and definition"""
    name=models.CharField(max_length=200, unique=True)
    max_runner=models.IntegerField() # Max runner for this queue
    node=models.ForeignKey(JobRunnerNode)

class FifoJobQueueConfig(JobQueueConfig):
    pass
