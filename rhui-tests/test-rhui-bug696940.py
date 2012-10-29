#! /usr/bin/python -tt

import argparse
import nose

from rhuilib.util import *
from rhuilib.rhuisetup import *
from rhuilib.rhuimanager import *
from rhuilib.rhuimanager_cds import *
from rhuilib.rhuimanager_client import *
from rhuilib.rhuimanager_repo import *
from rhuilib.rhuimanager_sync import *
from rhuilib.rhuimanager_identity import *
from rhuilib.rhuimanager_users import *
from rhuilib.rhuimanager_entitlements import *

class test_bug_696940:
    def __init__(self):
        argparser = argparse.ArgumentParser(description='RHUI bug 696940')
        args = argparser.parse_args()
        self.rs = RHUIsetup()
        self.rs.setup_from_rolesfile()
        
    def test_01_initial_run(self):
        RHUIManager.initial_run(self.rs.RHUA)

    def test_02_add_custom_repos(self):
        RHUIManagerRepo.add_custom_repo(self.rs.RHUA, "custom_repo1", "protected repo1", "/protected/x86_64/os", "1", "y", "/protected/$basearch/os")

    def test_03_delete_custom_repo(self):
        RHUIManagerRepo.delete_repo(self.rs.RHUA, ["protected repo1"])


if __name__ == "__main__":
    nose.run(defaultTest=__name__, argv=[__file__, '-v'])