#! /usr/bin/python -tt

import argparse
import nose
import time

from rhuilib.util import *
from rhuilib.rhuisetup import *
from rhuilib.rhuimanager import *
from rhuilib.rhuimanager_cds import *
from rhuilib.rhuimanager_client import *
from rhuilib.rhuimanager_repo import *
from rhuilib.rhuimanager_sync import *
from rhuilib.rhuimanager_entitlements import *


class test_rhui_update_simple(object):
    def __init__(self):
        argparser = argparse.ArgumentParser(description='Update RHUI packages from access.redhat.com')
        argparser.add_argument('--cert',
                               help='use supplied RH enablement certificate')
        args = argparser.parse_args()
        self.cert = args.cert
        if not self.cert:
            raise nose.exc.SkipTest("can't test without RH certificate")
        self.rs = RHUIsetup()
        self.rs.setup_from_rolesfile()

    def __del__(self):
        self.rs.__del__()

    def test_01_initial_run(self):
        ''' Do initial rhui-manager run'''
        RHUIManager.initial_run(self.rs.RHUA)

    def test_02_add_cds(self):
        ''' Add cds '''
        RHUIManagerCds.add_cds(self.rs.RHUA, "Cluster1", self.rs.CDS[0].hostname)

    def test_03_upload_content_cert(self):
        ''' Upload RH content certificate '''
        RHUIManagerEntitlements.upload_content_cert(self.rs.RHUA, self.cert)

    def test_04_add_rh_repo_by_repo(self):
        ''' Add rh repo '''
        RHUIManagerRepo.add_rh_repo_by_repo(self.rs.RHUA, ["Red Hat Update Infrastructure 2 \(RPMs\) \(6Server-x86_64\)"])

    def test_05_associate_repo_cds(self):
        ''' Associate repos with cluster '''
        RHUIManagerCds.associate_repo_cds(self.rs.RHUA, "Cluster1", ["Red Hat Update Infrastructure 2 \(RPMs\) \(6Server-x86_64\)"])

    def test_06_cli_remove_conf_rpm(self):
        ''' Remove rhui configuration rpm from RHUA '''
        Util.remove_conf_rpm(self.rs.RHUA)

    def test_07_sync_repo(self):
        ''' Sync RH repo '''
        RHUIManagerSync.sync_repo(self.rs.RHUA, ["Red Hat Update Infrastructure 2 \(RPMs\) \(6Server-x86_64\)"])
        reposync = ["In Progress", "", ""]
        while reposync[0] == "In Progress":
            time.sleep(10)
            reposync = RHUIManagerSync.get_repo_status(self.rs.RHUA, "Red Hat Update Infrastructure 2 \(RPMs\) \(6Server-x86_64\)")
        nose.tools.assert_equal(reposync[2], "Success")

    def test_08_sync_cds(self):
        ''' Sync cds '''
        RHUIManagerSync.sync_cds(self.rs.RHUA, [self.rs.CDS[0].hostname])
        cdssync = ["UP", "In Progress", "", ""]
        while cdssync[1] == "In Progress":
            time.sleep(10)
            cdssync = RHUIManagerSync.get_cds_status(self.rs.RHUA, self.rs.CDS[0].hostname)
        nose.tools.assert_equal(cdssync[3], "Success")

    def test_09_generate_ent_cert(self):
        ''' Generate entitlement certificate '''
        RHUIManagerClient.generate_ent_cert(self.rs.RHUA, "Cluster1", ["Red Hat Update Infrastructure 2 \(RPMs\)"], "cert-repo1", "/root/", validity_days="", cert_pw=None)

    def test_10_create_conf_rpm(self):
        ''' Create configuration rpm '''
        RHUIManagerClient.create_conf_rpm(self.rs.RHUA, "Cluster1", self.rs.CDS[0].hostname, "/root", "/root/cert-repo1.crt", "/root/cert-repo1.key", "repo1", "3.0")

    def test_11_install_conf_rpm_client(self):
        ''' Install configuration rpm to RHUA '''
        self.rs.RHUA.sftp.get("/root/repo1-3.0/build/RPMS/noarch/repo1-3.0-1.noarch.rpm", "/root/repo1-3.0-1.noarch.rpm")
        Util.install_rpm_from_master(self.rs.RHUA, "/root/repo1-3.0-1.noarch.rpm")

    def test_12_update(self):
        ''' Upgrade RHUI '''
        Expect.enter(self.rs.RHUA, "yum -y update && echo SUCCESS")
        Expect.expect(self.rs.RHUA, "[^ ]SUCCESS", 120)

    def test_13_remove_cds(self):
        ''' Remove cds '''
        RHUIManagerCds.delete_cds(self.rs.RHUA, "Cluster1", [self.rs.CDS[0].hostname])

    def test_14_delete_rh_repo(self):
        ''' Delete RH repo '''
        RHUIManagerRepo.delete_repo(self.rs.RHUA, ["Red Hat Update Infrastructure 2 \(RPMs\) \(6Server-x86_64\)"])

    def test_15_delete_rh_cert(self):
        ''' Remove RH certs from RHUI '''
        RHUIManager.remove_rh_certs(self.rs.RHUA)

    def test_16_cli_remove_conf_rpm(self):
        ''' Remove rhui configuration rpm from RHUA '''
        Util.remove_conf_rpm(self.rs.RHUA)


if __name__ == "__main__":
    nose.run(defaultTest=__name__, argv=[__file__, '-v'])