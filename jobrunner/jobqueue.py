# -*- coding: utf-8 -*-
"""
Generic job queue

@author: Sébastien Renard (sebastien.renard@digitalfox.org)
@license:GNU GPL V3
"""

from threading import Lock

class JobQueue:
    """A generic job queue - every JobQueue plugin inherit from this class"""
    def __init__(self, qConfig):
        """@param jobQueueConfig: a JobQueueConfig object"""
        self.qConfig=qConfig
        self.locker=Lock()
        self.jobs=[]

    def add(self, job):
        self.locker.acquire()
        self.jobs.append(job)
        self.locker.release()

    def get(self):
        self.locker.acquire()
        job=None
        try:
            if not self.isEmpty():
                job=self._get()
        finally:
            self.locker.release()
        return job

    def clear(self):
        self.locker.acquire()
        self.jobs=[]
        self.locker.release()

    def isEmpty(self):
        if len(self)==0:
            return True
        else:
            return False

    def __len__(self):
        return len(self.jobs)

    def _get(self):
        """This method must be overriden by subclass"""
        raise NotImplementedError