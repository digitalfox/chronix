#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Jobrunner is composed of two parts
- the job dispatcher that listen to activity resolver request and fill job queue
- job runners that pop jobs from queue to execute and control process

@author: Sébastien Renard (sebastien.renard@digitalfox.org)
@license:GNU GPL V3
"""

# Python imports
from time import sleep
from threading import Lock, Thread
import sys
from os.path import abspath, dirname, join, pardir
import random

## Setup django envt & django imports
sys.path.append(abspath(join(dirname(__file__), pardir)))
from django.core.management import setup_environ
import settings
setup_environ(settings)

# Chronix imports
from chronix.jobrunner.models import JobRunnerNode

RUNNER_INTERVAL=2 # In seconds

class JobDispatcher(Thread):
    """A thread running the job dispatcher"""
    def __init__(self, queues):
        self.queues=queues # Queues managed by this dispatcher
        self.stop=False  # Flag used to stop thread
        Thread.__init__(self)

    def run(self):
        """Method executed when the thread object start() method is called"""
        print "job dispatcher starting"
        self.loop()
        print "job dispatcher stopped"

    def loop(self):
        # Dispatcher loop
        i=0
        while not self.stop:
            i+=1
            self.queues[0].add("lala %s" % i)  # Fake job
            self.queues[1].add("toto %s" % i)  # Fake job
            sleep(0.3)

class JobRunnerNodeThread(Thread):
    """Jobrunner manager"""
    def __init__(self, node):
        self.node=node
        self.stop=False  # Flag used to stop node
        self.queues=[] # Queues managed by this node
        self.runners=[] # Runners managed by this node

        # Create job queues
        for qConfig in node.jobqueueconfig_set.all():
            try:
                qType=eval(qConfig.algorithm.class_name)
                queue=qType(qConfig)
                self.queues.append(queue)
            except NameError, e:
                print e

        # Create the job dispatcher that feed queues
        self.dispatcher=JobDispatcher(self.queues)
        self.dispatcher.start()
        Thread.__init__(self)

    def run(self):
        """Method executed when the thread object start() method is called"""
        print "Starting job runner node"
        self.loop()
        self.dispatcher.stop=True
        print "Job runner node stopped"

    def printStatus(self):
        # Runner status
        print "\n*******************"
        print "Runner status: %s/%s runners" % (len(self.runners), self.node.max_runner)
        for queue in self.queues:
            qRunners=self.getQueueRunners(queue)
            print "Queue %s status : %s jobs in queue - %s/%s runners " % \
                (queue.qConfig.name, len(queue), len(qRunners), queue.qConfig.max_runner)

    def cleanupRunners(self):
        # Cleanup finished runners
        for runner in self.runners:
            if not runner.isAlive():
                print "Runner %s finished his job" % runner.getName()
                self.runners.remove(runner)

    def getQueueRunners(self, queue):
        return [runner for runner in self.runners if runner.queue==queue]

    def loop(self):
        """Main runner loop."""
        while not self.stop:
            self.cleanupRunners()
            self.printStatus()
            if len(self.runners)>=self.node.max_runner:
                sleep(RUNNER_INTERVAL)
                continue
            # Get new jobs from queues
            for queue in self.queues:
                qRunners=self.getQueueRunners(queue)
                while len(qRunners) < queue.qConfig.max_runner and \
                      len(self.runners)<self.node.max_runner and \
                      not queue.isEmpty():
                    # Launch runners
                    print "Creating new runner"
                    runner=JobRunner(queue.get(), queue)
                    self.runners.append(runner)
                    qRunners=self.getQueueRunners(queue) # Compute qRunners for next loop
                    runner.start()
            sleep(RUNNER_INTERVAL)


class JobRunner(Thread):
    """A thread running a job runner"""
    def __init__(self, job, queue):
        self.job=job
        self.queue=queue # Needed to check max runner for each queue
        Thread.__init__(self)

    def run(self):
        print "Runner is executing job %s" % self.job
        #TODO: notify the activity resolver of job status (start, end)
        # Fake job running
        import random
        sleep(random.randint(15, 30))

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

class FifoJobQueue(JobQueue):
    """A simple fifo job queue
    @todo: Make this class a plugin once plugin architecture defined"""
    def _get(self):
        if not self.isEmpty():
            job=self.jobs.pop(0)
        else:
            job=None
        return job

class RandomJobQueue(JobQueue):
    """A simple random job queue.
    @todo: Make this class a plugin once plugin architecture defined"""
    def _get(self):
        if not self.isEmpty():
            r=random.randint(0, len(self)-1)
            job=self.jobs.pop(r)
        else:
            job=None
        return job

def main():
    try:
        node=JobRunnerNode.objects.get(name=sys.argv[1])
        t=JobRunnerNodeThread(node)
        t.start()
        sleep(60)
        t.stop=True
    except IndexError:
        print "JobRunner node name must be given in argument"
        sys.exit(1)
    except JobRunnerNode.DoesNotExist:
        print "No job runner node  with such name"
        print "Job runners node available: %s" % ", ".join([unicode(t) for t in JobRunnerNode.objects.all()])
        sys.exit(1)

if __name__ == "__main__":
    main()
