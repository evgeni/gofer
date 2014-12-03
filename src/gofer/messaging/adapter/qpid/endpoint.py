#
# Copyright (c) 2011 Red Hat, Inc.
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

"""
AMQP endpoint base classes.
"""
from logging import getLogger

from qpid.messaging import Disposition, RELEASED, REJECTED

from gofer.messaging.adapter.model import BaseEndpoint
from gofer.messaging.adapter.qpid.connection import Connection


log = getLogger(__name__)


class Endpoint(BaseEndpoint):
    """
    Base class for an AMQP endpoint.
    :ivar _connection: An AMQP session.
    :type _connection: qpid.messaging.Channel
    :ivar _channel: An AMQP session.
    :type _channel: qpid.messaging.Session
    """

    def __init__(self, url):
        """
        :param url: The broker url <adapter>://<user>/<pass>@<host>:<port>.
        :type url: str
        """
        BaseEndpoint.__init__(self, url)
        self._connection = None
        self._channel = None

    def channel(self):
        """
        Get a session for the open connection.
        :return: An open session.
        :rtype: qpid.messaging.Session
        """
        return self._channel

    def ack(self, message):
        """
        Acknowledge all messages received on the session.
        :param message: The message to acknowledge.
        :type message: qpid.messaging.Message
        """
        self._channel.acknowledge(message=message)

    def reject(self, message, requeue=True):
        """
        Reject the specified message.
        :param message: The message to reject.
        :type message: qpid.messaging.Message
        :param requeue: Requeue the message or discard it.
        :type requeue: bool
        """
        if requeue:
            disposition = Disposition(RELEASED)
        else:
            disposition = Disposition(REJECTED)
        self._channel.acknowledge(message=message, disposition=disposition)

    def open(self):
        """
        Open the endpoint.
        """
        connection = Connection(self.url)
        connection.open()
        self._connection = connection
        self._channel = connection.channel()

    def close(self, hard=False):
        """
        Close the endpoint.
        :param hard: Force the connection closed.
        :type hard: bool
        """
        self._channel.close()
        self._connection.close(hard)

    def __str__(self):
        return 'Endpoint id:%s broker @ %s' % (self.id(), self.url)
