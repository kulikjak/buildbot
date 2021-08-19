# This file is part of Buildbot.  Buildbot is free software: you can
# redistribute it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, version 2.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# Copyright Buildbot Team Members

import os
from unittest.case import SkipTest

from twisted.internet import defer

from buildbot.test.util.integration import RunMasterBase

from .interop.test_commandmixin import CommandMixinMasterPB
from .interop.test_compositestepmixin import CompositeStepMixinMasterPb
from .interop.test_integration_secrets import SecretsConfigPB
from .interop.test_interruptcommand import InterruptCommandPb
from .interop.test_setpropertyfromcommand import SetPropertyFromCommandPB
from .interop.test_transfer import TransferStepsMasterPb
from .interop.test_worker_reconnect import WorkerReconnect

# This integration test puts HTTP proxy in between the master and worker. You
# need to have a local proxy server for this to work.

# If you want to run this,
# export BUILDBOT_TEST_PROXY_CONNECTION_STRING='tcp:127.0.0.1:port'


class RunMasterBehindProxy(RunMasterBase):

    def setUp(self):
        if "BUILDBOT_TEST_PROXY_CONNECTION_STRING" not in os.environ:
            raise SkipTest(
                "HTTP proxy related integration tests only run when environment"
                " variable BUILDBOT_TEST_PROXY_CONNECTION_STRING is set ")

    @defer.inlineCallbacks
    def setupConfig(self, config_dict, startWorker=True):

        proxy_connection_string = os.environ.get('BUILDBOT_TEST_PROXY_CONNECTION_STRING')
        yield RunMasterBase.setupConfig(self, config_dict, startWorker,
                                        proxy_connection_string=proxy_connection_string)


# Use interoperability test cases to test the HTTP proxy tunneling.

class ProxyCommandMixinMasterPB(RunMasterBehindProxy, CommandMixinMasterPB):
    timeout = 5


class ProxyCompositeStepMixinMasterPb(RunMasterBehindProxy, CompositeStepMixinMasterPb):
    timeout = 5


class ProxyInterruptCommandPb(RunMasterBehindProxy, InterruptCommandPb):
    timeout = 5


class ProxySecretsConfigPB(RunMasterBehindProxy, SecretsConfigPB):
    timeout = 5


class ProxySetPropertyFromCommandPB(RunMasterBehindProxy, SetPropertyFromCommandPB):
    timeout = 5


class ProxyTransferStepsMasterPb(RunMasterBehindProxy, TransferStepsMasterPb):
    # proxy is slower in transferring large files
    timeout = 30


class ProxyWorkerReconnect(RunMasterBehindProxy, WorkerReconnect):
    timeout = 5
