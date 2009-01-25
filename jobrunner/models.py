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

    def __unicode__(self):
        return self.name

class JobQueueAlgorithm(models.Model):
    """Job algorithm declaration"""
    name=models.CharField(max_length=200, unique=True)
    class_name=models.CharField(max_length=200, unique=True)

    def __unicode__(self):
        return self.name

class JobQueueConfig(models.Model):
    """Generic job queue configuration and definition"""
    name=models.CharField(max_length=200, unique=True)
    max_runner=models.IntegerField() # Max runner for this queue
    node=models.ForeignKey(JobRunnerNode)
    algorithm=models.ForeignKey(JobQueueAlgorithm)
    param=models.CharField(max_length=2000, blank=True, null=True) # extra job queue parameters

    def __unicode__(self):
        return self.name
