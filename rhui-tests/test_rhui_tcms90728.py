#! /usr/bin/python -tt

import nose
import re

from rhuilib.util import *
from rhuilib.rhui_testcase import *
from rhuilib.rhuimanager import *
from rhuilib.rhuimanager_repo import *
from rhuilib.rhuimanager_entitlements import *
from rhuilib.pulp_admin import *

class test_rhui_tcms90728(RHUITestcase, RHUI_has_RH_cert):
    def _setup(self):
        '''[TCMS#90728 setup] Do initial rhui-manager run'''
        RHUIManager.initial_run(self.rs.Instances["RHUA"][0])

        '''[TCMS#90728 setup] Upload RH content certificate '''
        RHUIManagerEntitlements.upload_content_cert(self.rs.Instances["RHUA"][0], self.cert)

        '''[TCMS#90728 setup] Create repos'''
        RHUIManagerRepo.add_custom_repo(self.rs.Instances["RHUA"][0], "repo1")
        RHUIManagerRepo.add_custom_repo(self.rs.Instances["RHUA"][0], "repo2")
        RHUIManagerRepo.add_rh_repo_by_repo(self.rs.Instances["RHUA"][0], ["Red Hat Enterprise Linux 6 Server - Supplementary from RHUI \(RPMs\) \(6Server-i386\)"])
        
        '''[TCMS#90728 setup] Sync RH repo '''
        self._sync_repo(["Red Hat Enterprise Linux 6 Server - Supplementary from RHUI \(RPMs\) \(6Server-i386\)"])
        
        '''[TCMS#90728 setup] Upload content'''
        Expect.ping_pong(self.rs.Instances["RHUA"][0], "mkdir /root/rpms90728 && echo SUCCESS", "[^ ]SUCCESS")
        self.rs.Instances["RHUA"][0].sftp.put("/usr/share/rhui-testing-tools/testing-data/custom-signed-rpm-1-0.1.fc17.noarch.rpm", "/root/rpms90728/custom-signed-rpm-1-0.1.fc17.noarch.rpm")
        self.rs.Instances["RHUA"][0].sftp.put("/usr/share/rhui-testing-tools/testing-data/custom-unsigned-rpm-1-0.1.fc17.noarch.rpm", "/root/rpms90728/custom-unsigned-rpm-1-0.1.fc17.noarch.rpm")
        RHUIManagerRepo.upload_content(self.rs.Instances["RHUA"][0], ["repo1"], "/root/rpms90728")

    def _test(self):
        '''[TCMS#90728 test] Check the packages list'''
        nose.tools.assert_equal(RHUIManagerRepo.check_for_package(self.rs.Instances["RHUA"][0], "repo1", ""), ["custom-signed-rpm-1-0.1.fc17.noarch.rpm", "custom-unsigned-rpm-1-0.1.fc17.noarch.rpm"])
        nose.tools.assert_equal(RHUIManagerRepo.check_for_package(self.rs.Instances["RHUA"][0], "repo1", "custom-unsigned"), ["custom-unsigned-rpm-1-0.1.fc17.noarch.rpm"])
        nose.tools.assert_equal(RHUIManagerRepo.check_for_package(self.rs.Instances["RHUA"][0], "repo1", "test"), [])
        nose.tools.assert_equal(RHUIManagerRepo.check_for_package(self.rs.Instances["RHUA"][0], "repo2", ""), [])
        actual_answer = RHUIManagerRepo.check_for_package(self.rs.Instances["RHUA"][0], "Red Hat Enterprise Linux 6 Server - Supplementary from RHUI \(RPMs\) \(6Server-i386\)", "")
        nose.tools.ok_('Package Count' in actual_answer[0])


    def _cleanup(self):
        '''[TCMS#90728 cleanup] Remove a repo'''
        RHUIManagerRepo.delete_repo(self.rs.Instances["RHUA"][0], ["repo1"])
        RHUIManagerRepo.delete_repo(self.rs.Instances["RHUA"][0], ["repo2"])
        RHUIManagerRepo.delete_repo(self.rs.Instances["RHUA"][0], ["Red Hat Enterprise Linux 6 Server - Supplementary from RHUI \(RPMs\) \(6Server-i386\)"])
        
        '''[TCMS#90728 cleanup] Remove rpms from RHUI '''
        Expect.ping_pong(self.rs.Instances["RHUA"][0], " rm -f -r /root/rpms90728 && echo SUCCESS", "[^ ]SUCCESS")

        '''[TCMS#90728 cleanup] Remove RH certificate from RHUI'''
        RHUIManager.remove_rh_certs(self.rs.Instances["RHUA"][0])
        
if __name__ == "__main__":
    nose.run(defaultTest=__name__, argv=[__file__, '-v'])
