#! /usr/bin/python -tt

import nose
import re

from rhuilib.util import *
from rhuilib.rhui_testcase import *
from rhuilib.rhuimanager import *
from rhuilib.rhuimanager_cds import *
from rhuilib.rhuimanager_repo import *
from rhuilib.rhuimanager_client import *
from rhuilib.pulp_admin import *

class test_rhui_tcms90934(RHUITestcase):
    def _setup(self):
        '''[TCMS#90934 setup] Do initial rhui-manager run'''
        RHUIManager.initial_run(self.rs.Instances["RHUA"][0])

        '''[TCMS#90934 setup] Add cds'''
        RHUIManagerCds.add_cds(self.rs.Instances["RHUA"][0], "Cluster1", self.rs.Instances["CDS"][0].private_hostname)
        
        '''[TCMS#90934 setup] Create custom repo'''
        RHUIManagerRepo.add_custom_repo(self.rs.Instances["RHUA"][0], "repo1")
        
        '''[TCMS#90934 setup] Associate repo with cluster'''
        RHUIManagerCds.associate_repo_cds(self.rs.Instances["RHUA"][0], "Cluster1", ["repo1"])
        
    def _test(self):
        '''[TCMS#90934 test] Generate entitlement certificate'''
        RHUIManagerClient.generate_ent_cert(self.rs.Instances["RHUA"][0], "Cluster1", ["repo1"], "cert-repo1", "/root/", validity_days="", cert_pw=None)

    def _cleanup(self):
        '''[TCMS#90934 cleanup] Remove cds'''
        RHUIManagerCds.delete_cds(self.rs.Instances["RHUA"][0], "Cluster1", [self.rs.Instances["CDS"][0].private_hostname])
        
        '''[TCMS#90934 cleanup] Remove custom repo'''
        RHUIManagerRepo.delete_repo(self.rs.Instances["RHUA"][0], ["repo1"])
        
if __name__ == "__main__":
    nose.run(defaultTest=__name__, argv=[__file__, '-v'])

