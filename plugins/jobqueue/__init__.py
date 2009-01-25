# -*- coding: utf-8 -*-
"""
Chronix job queue plugins for job queue algorithm.
This plugin is not a django apps and then should *not* be declared in settings.py

Plugin structure:
- each module can contain one or more class that must derive from jobrunner.jobrunner.JobQueue
 
@author: Sébastien Renard (sebastien.renard@digitalfox.org)
@license:GNU GPL V3
"""
