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
from time import sleep, strftime
from threading import Thread
import sys
from os.path import abspath, dirname, join, pardir
from subprocess import Popen

## Setup django envt & django imports
sys.path.append(abspath(join(dirname(__file__), pardir)))
from django.core.management import setup_environ
import settings
setup_environ(settings)

# Chronix imports
from chronix.jobrunner.models import JobRunnerNode
from chronix.plugins.helpers import loadPlugin, ChronixPluginException

#TODO: move that in database or file
RUNNER_INTERVAL=2 # In seconds
PROCESS_POLLING_INTERVAL=1 # In seconds
JOB_STDOUT_DIR="stdout" # relative path is a bad idea


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
            self.queues[0].add(Job("lala %s" % i, "echo lala %s;sleep 10" % i))  # Fake job
            self.queues[1].add(Job("toto %s" % i, "echo toto %s;sleep 5;balbla" % i))  # Fake job
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
                qType=loadPlugin("jobqueue", qConfig.algorithm.class_name)
                queue=qType(qConfig)
                self.queues.append(queue)
            except ChronixPluginException, e:
                print e
                print "Queue %s disabled" % qConfig.name

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


class Job:
    """Fake job structure. Real one will be done once
    more work have been done on repo and activity resolver modules"""
    def __init__(self, name, prog, env=dict()):
        self.name=name
        self.prog=prog
        self.env=env

class JobRunner(Thread):
    """A thread running a job runner"""
    def __init__(self, job, queue):
        Thread.__init__(self)
        self.job=job
        self.queue=queue # Needed to check max runner for each queue
        self.process=None # The process manage by this runner (Popen object)
        stdoutName="%s-%s-%s-%s" % (queue.qConfig.node.name, queue.qConfig.name, self.getName(), strftime("%Y%m%d%H%M%S")) 
        self.stdout=file(join(JOB_STDOUT_DIR, stdoutName), "w") # The process stdout on disk

    def run(self):
        """Method executed when the thread object start() method is called"""
        print "Runner is executing job %s" % self.job.name
        self.process=Popen(self.job.prog, stdout=self.stdout, stderr=self.stdout, shell=True, env=self.job.env)
        self._wait()
        print "Runner finished to execute job %s with rc %s" % (self.job.name, self.process.returncode)
        # Close stdout file
        self.stdout.close()
        self._notify()

    def _wait(self):
        """Wait process ending"""
        while True:
            if self.process.poll() is not None:
                break
            sleep(PROCESS_POLLING_INTERVAL)

    def _notify(self):
        """Notify the job is finished"""
        pass  #Nothing for now. Shoud be connected to activity resolver

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
