#! /usr/bin/python -tt

import nose
import re

from stitches.expect import *
from rhuilib.util import *
from rhuilib.rhui_testcase import *
from rhuilib.rhuimanager import *
from rhuilib.rhuimanager_cds import *
from rhuilib.rhuimanager_client import *
from rhuilib.rhuimanager_repo import *
from rhuilib.rhuimanager_sync import *
from rhuilib.rhuimanager_entitlements import *


class Cds(object):
    repos_path = '/var/lib/pulp-cds/repos'

    def __init__(self, connection, clientname=None, displayname=None):
        self.connection = connection
        self.hostname = connection.private_hostname
        if clientname is None:
            self.clientname = self.hostname
        if displayname is None:
            self.displayname = self.hostname

    def get_reponames(self):
        '''return list of names made of contents of /var/lib/pulp-cds/repos'''
        (stdin, stdout, stderr) = self.connection.exec_command(
            "ls %s" % self.repos_path)
        return [x.strip() for x in stdout.read().split('\n')]


class test_tcms_178468(RHUITestcase):
    repo = "repo-1"
    cluster = "cluster-1"

    def _setup(self):
        self.cds = Cds(self.rs.Instances["CDS"][0])

        '''[TCMS#178468 setup] Do initial rhui-manager run'''
        RHUIManager.initial_run(self.rs.Instances["RHUA"][0])

        '''[TCMS#178468 setup] Add cds creating a cluster'''
        RHUIManagerCds.add_cds(self.rs.Instances["RHUA"][0], self.cluster, self.cds.hostname)

        '''[TCMS#178468 setup] Create custom repo'''
        RHUIManagerRepo.add_custom_repo(self.rs.Instances["RHUA"][0], self.repo)

        '''[TCMS#178468 setup] Associate custom repo with a cluster'''
        RHUIManagerCds.associate_repo_cds(self.rs.Instances["RHUA"][0], self.cluster, [self.repo])

        '''[TCMS#178468 setup] Upload content to custom repo '''
        RHUIManagerRepo.upload_content(self.rs.Instances["RHUA"][0], [self.repo], "/etc/rhui/confrpm")

        '''[TCMS#178468 setup] Sync cds having uploaded content'''
        self._sync_cds([self.cds.hostname])

    def _test(self):
        self.cds = Cds(self.rs.Instances["CDS"][0])

        '''[TCMS#178468 test] assert repo contents is present on the CDS'''
        nose.tools.ok_(self.repo in self.cds.get_reponames())

        '''[TCMS#178468 test] Un-associate a custom repo from a cluster'''
        RHUIManagerCds.unassociate_repo_cds(self.rs.Instances["RHUA"][0], self.cluster, [self.repo])

        '''[TCMS#178468 test] Sync cds having unassociated repo'''
        self._sync_cds([self.cds.hostname])

        '''[TCMS#178468 test] assert repo contents is present on the CDS no more'''
        nose.tools.ok_(self.repo not in self.cds.get_reponames())

    def _cleanup(self):
        '''[TCMS#178468 teardown] Remove the custom repo'''
        RHUIManagerRepo.delete_repo(self.rs.Instances["RHUA"][0], [self.repo])

        """[TCMS#178468 teardown] check removing a cds from single node cluster"""
        RHUIManagerCds.delete_cds(self.rs.Instances["RHUA"][0], "cluster-1", [self.rs.Instances["CDS"][0].private_hostname])


if __name__ == "__main__":
    nose.run(defaultTest=__name__, argv=[__file__, '-v'])
