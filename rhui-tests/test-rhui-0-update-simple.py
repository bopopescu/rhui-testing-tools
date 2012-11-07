#! /usr/bin/python -tt

import nose
import time

from rhuilib.util import *
from rhuilib.rhui_testcase import *
from rhuilib.rhuimanager import *
from rhuilib.rhuimanager_cds import *
from rhuilib.rhuimanager_client import *
from rhuilib.rhuimanager_repo import *
from rhuilib.rhuimanager_sync import *
from rhuilib.rhuimanager_entitlements import *


class test_rhui_update_simple(RHUITestcase):
    def __init__(self):
        RHUITestcase.__init__(self)
        if not 'rhcert' in self.rs.config.keys():
            raise nose.exc.SkipTest("can't test without RH certificate")
        self.cert = self.rs.config['rhcert']

    def test_01_initial_run(self):
        '''[Update Simple setup] Do initial rhui-manager run'''
        RHUIManager.initial_run(self.rs.RHUA)

    def test_02_add_cds(self):
        '''[Update Simple setup] Add cds '''
        RHUIManagerCds.add_cds(self.rs.RHUA, "Cluster1", self.rs.CDS[0].hostname)

    def test_03_upload_content_cert(self):
        '''[Update Simple setup] Upload RH content certificate '''
        RHUIManagerEntitlements.upload_content_cert(self.rs.RHUA, self.cert)

    def test_04_add_rh_repo_by_repo(self):
        '''[Update Simple setup] Add rh repo '''
        RHUIManagerRepo.add_rh_repo_by_repo(self.rs.RHUA, ["Red Hat Update Infrastructure 2 \(RPMs\) \(6Server-x86_64\)"])

    def test_05_associate_repo_cds(self):
        '''[Update Simple setup] Associate repos with cluster '''
        RHUIManagerCds.associate_repo_cds(self.rs.RHUA, "Cluster1", ["Red Hat Update Infrastructure 2 \(RPMs\) \(6Server-x86_64\)"])

    def test_06_cli_remove_conf_rpm(self):
        '''[Update Simple setup] Remove rhui configuration rpm from RHUA '''
        Util.remove_conf_rpm(self.rs.RHUA)

    def test_07_sync_repo(self):
        '''[Update Simple setup] Sync RH repo '''
        RHUIManagerSync.sync_repo(self.rs.RHUA, ["Red Hat Update Infrastructure 2 \(RPMs\) \(6Server-x86_64\)"])
        reposync = ["In Progress", "", ""]
        while reposync[0] == "In Progress":
            time.sleep(10)
            reposync = RHUIManagerSync.get_repo_status(self.rs.RHUA, "Red Hat Update Infrastructure 2 \(RPMs\) \(6Server-x86_64\)")
        nose.tools.assert_equal(reposync[2], "Success")

    def test_08_sync_cds(self):
        '''[Update Simple setup] Sync cds '''
        RHUIManagerSync.sync_cds(self.rs.RHUA, [self.rs.CDS[0].hostname])
        cdssync = ["UP", "In Progress", "", ""]
        while cdssync[1] == "In Progress":
            time.sleep(10)
            cdssync = RHUIManagerSync.get_cds_status(self.rs.RHUA, self.rs.CDS[0].hostname)
        nose.tools.assert_equal(cdssync[3], "Success")

    def test_09_generate_ent_cert(self):
        '''[Update Simple setup] Generate entitlement certificate '''
        RHUIManagerClient.generate_ent_cert(self.rs.RHUA, "Cluster1", ["Red Hat Update Infrastructure 2 \(RPMs\)"], "cert-repo1", "/root/", validity_days="", cert_pw=None)

    def test_10_create_conf_rpm(self):
        '''[Update Simple setup] Create configuration rpm '''
        RHUIManagerClient.create_conf_rpm(self.rs.RHUA, "Cluster1", self.rs.CDS[0].hostname, "/root", "/root/cert-repo1.crt", "/root/cert-repo1.key", "repo1", "3.0")

    def test_11_install_conf_rpm_client(self):
        '''[Update Simple setup] Install configuration rpm to RHUA '''
        self.rs.RHUA.sftp.get("/root/repo1-3.0/build/RPMS/noarch/repo1-3.0-1.noarch.rpm", "/root/repo1-3.0-1.noarch.rpm")
        Util.install_rpm_from_master(self.rs.RHUA, "/root/repo1-3.0-1.noarch.rpm")

    def test_12_update(self):
        '''[Update Simple test] Upgrade RHUI '''
        Expect.ping_pong(self.rs.RHUA, "yum -y update && echo SUCCESS", "[^ ]SUCCESS", 120)

    def test_13_remove_cds(self):
        '''[Update Simple cleanup] Remove cds '''
        RHUIManagerCds.delete_cds(self.rs.RHUA, "Cluster1", [self.rs.CDS[0].hostname])

    def test_14_delete_rh_repo(self):
        '''[Update Simple cleanup] Delete RH repo '''
        RHUIManagerRepo.delete_repo(self.rs.RHUA, ["Red Hat Update Infrastructure 2 \(RPMs\) \(6Server-x86_64\)"])

    def test_15_delete_rh_cert(self):
        '''[Update Simple cleanup] Remove RH certs from RHUI '''
        RHUIManager.remove_rh_certs(self.rs.RHUA)

    def test_16_cli_remove_conf_rpm(self):
        '''[Update Simple cleanup] Remove rhui configuration rpm from RHUA '''
        Util.remove_conf_rpm(self.rs.RHUA)


if __name__ == "__main__":
    nose.run(defaultTest=__name__, argv=[__file__, '-v'])
