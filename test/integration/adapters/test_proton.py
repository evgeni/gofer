# Copyright (c) 2013 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public
# License as published by the Free Software Foundation; either version
# 2 of the License (GPLv2) or (at your option) any later version.
# There is NO WARRANTY for this software, express or implied,
# including the implied warranties of MERCHANTABILITY,
# NON-INFRINGEMENT, or FITNESS FOR A PARTICULAR PURPOSE. You should
# have received a copy of GPLv2 along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.


from logging import basicConfig

from base import Test

from gofer.messaging.adapter.factory import Loader


basicConfig()

URL = 'amqp://localhost'


def run():
    loader = Loader()
    loader.load()
    # amqp-1-0
    adapter = loader.catalog['amqp-1-0']
    test = Test(URL, adapter)
    test.test_crud()
    test.test_no_exchange()
    # proton
    adapter = loader.catalog['proton']
    test = Test(URL, adapter)
    test.test_crud()
    test.test_no_exchange()


if __name__ == '__main__':
    run()
