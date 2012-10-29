#! /usr/bin/python -tt

import argparse
import nose

from rhuilib.expect import *
from rhuilib.rhuisetup import *
from rhuilib.rhuimanager import *
from rhuilib.rhuimanager_cds import *
from rhuilib.rhuimanager_repo import *

class test_bug_789054:
    def __init__(self):
        argparser = argparse.ArgumentParser(description='RHUI bug 789054')
        args = argparser.parse_args()
        self.rs = RHUIsetup()
        self.rs.setup_from_rolesfile()

    def test_01_initial_run(self):
        RHUIManager.initial_run(self.rs.RHUA)

    def test_02_add_cds(self):
        RHUIManagerCds.add_cds(self.rs.RHUA, "Cluster1", self.rs.CDS[0].hostname)

    def test_03_add_custom_repos(self):
        RHUIManagerRepo.add_custom_repo(self.rs.RHUA, "repo1")
        RHUIManagerRepo.add_custom_repo(self.rs.RHUA, "repo2")
        RHUIManagerRepo.add_custom_repo(self.rs.RHUA, "repo3")

    def test_04_associate_repo_cds(self):
        RHUIManagerCds.associate_repo_cds(self.rs.RHUA, "Cluster1", ["repo1", "repo2", "repo3"])

    def test_05_generate_ent_cert(self):
        RHUIManager.screen(self.rs.RHUA, "client")
        Expect.enter(self.rs.RHUA, "e")
        RHUIManager.select_one(self.rs.RHUA, "Cluster1")
        RHUIManager.select(self.rs.RHUA, ["repo1", "repo2"])
        Expect.expect(self.rs.RHUA, "Name of the certificate.*contained with it:")
        Expect.enter(self.rs.RHUA, "cert with spaces")
        Expect.expect(self.rs.RHUA, "The name can not contain spaces")

    def test_06_remove_cds(self):
        RHUIManagerCds.delete_cds(self.rs.RHUA, "Cluster1", [self.rs.CDS[0].hostname])

    def test_07_delete_custom_repo(self):
        RHUIManagerRepo.delete_repo(self.rs.RHUA, ["repo1", "repo2", "repo3"])


if __name__ == "__main__":
    nose.run(defaultTest=__name__, argv=[__file__, '-v'])