#
# Copyright (c) 2016 Red Hat, Inc.
#
# This software is licensed to you under the GNU Lesser General Public
# License as published by the Free Software Foundation; either version
# 2 of the License (LGPLv2) or (at your option) any later version.
# There is NO WARRANTY for this software, express or implied,
# including the implied warranties of MERCHANTABILITY,
# NON-INFRINGEMENT, or FITNESS FOR A PARTICULAR PURPOSE. You should
# have received a copy of LGPLv2 along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/lgpl-2.0.txt.
#
# Jeff Ortel <jortel@redhat.com>
#

from logging import getLogger
from time import sleep

from gofer.mp import Process, Pipe
from gofer.common import Thread
from gofer.rmi.context import Context
from gofer.rmi.model import protocol
from gofer.rmi.model.child import Call as Target


log = getLogger(__file__)


POLL = 0.10


class Call(protocol.Call):
    """
    The parent-side of the RMI call invoked in a child process.
    After the fork, the child invokes the method and relays events
    back using the inter-process queue.
    """

    def __call__(self):
        """
        Invoke the RMI as follows:
          - Fork
          - Start the monitor.
          - Read and dispatch reply messages.
        :return: Whatever method returned.
        """
        pipe = Pipe()
        target = Target(self.method, *self.args, **self.kwargs)
        child = Process(target, pipe)
        monitor = Monitor(Context.current(), child)
        try:
            child.start()
            monitor.start()
            pipe.writer.close()
            retval = self.read(pipe.reader)
            return retval
        finally:
            pipe.close()
            monitor.stop()
            child.wait()

    def read(self, pipe):
        """
        Read the reply queue and dispatch messages until *End* is raised..
        :param pipe: A message queue.
        :type  pipe: gofer.mp.Reader
        """
        while True:
            try:
                reply = protocol.Reply.read(pipe)
                reply()
            except protocol.End as end:
                return end.result


class Monitor(Thread):
    """
    Provides monitoring of cancellation.
    When cancel is detected, the child process is terminated.
    :ivar context: The RMI context.
    :type context: Context
    :ivar child: The child process.
    :type child: Process
    :ivar poll: Main polling loop boolean.
    :type poll: bool
    """

    NAME = 'monitor'
    POLL = 0.10

    def __init__(self, context, child):
        """
        :param context: The RMI context.
        :type  context: Context
        :param child: The child process.
        :type  child: Process
        """
        super(Monitor, self).__init__(name=Monitor.NAME)
        self.context = context
        self.child = child
        self.poll = True
        self.setDaemon(True)

    def stop(self):
        """
        Stop the thread.
        """
        self.poll = False
        self.join()

    def run(self):
        """
        Test for cancellation.
        When cancel is detected, the child process is terminated.
        """
        while self.poll:
            if self.context.cancelled():
                self.child.terminate()
                break
            else:
                sleep(Monitor.POLL)


class Result(protocol.Result):
    """
    Called when a RESULT message is received.
    """

    def __call__(self):
        """
        :raise End: always.
        """
        raise protocol.End(self.payload)


class Progress(protocol.Progress):
    """
    Called when a PROGRESS message is received.
    """

    def __call__(self):
        """
        Relay to RMI context progress reporter.
        """
        context = Context.current()
        context.progress.__dict__.update(self.payload.__dict__)
        context.progress.report()


class Error(protocol.Error):
    """
    Called when a ERROR message is received.
    """

    def __call__(self):
        """
        An exception is raised to report the error.
        :raise Exception: always.
        """
        raise Exception(self.payload)


class Raised(protocol.Raised):
    """
    Called when a RAISED (exception) message is received.
    """

    def __call__(self):
        """
        The reported exception is instantiated and raised.
        :raise Exception: always.
        """
        raise self.payload


class Ping(protocol.Ping):
    """
    Called when a PING message is received.
    """

    def __call__(self):
        """
        The reported exception is instantiated and raised.
        :raise Exception: always.
        """
        log.debug('pinged by %d', self.payload)


# register reply message handling.
protocol.Reply.register(Result.CODE, Result)
protocol.Reply.register(Progress.CODE, Progress)
protocol.Reply.register(Error.CODE, Error)
protocol.Reply.register(Raised.CODE, Raised)
protocol.Reply.register(Ping.CODE, Ping)
