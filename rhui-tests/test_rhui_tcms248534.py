#! /usr/bin/python -tt

import nose
import time
import subprocess

from rhuilib.util import *
from rhuilib.rhui_testcase import *
from rhuilib.rhuimanager import *


class test_tcms_248534(RHUITestcase):
    ''' Bug 916326 '''
    def _setup(self):
        '''[TCMS#248534 setup] Do initial rhui-manager run'''
        RHUIManager.initial_run(self.rs.Instances["RHUA"][0])

        '''[TCMS#248534 setup] Copy testing data'''
        subprocess.check_output(["scp", "-r", "-o", "StrictHostKeyChecking=no", "-o", "UserKnownHostsFile=/dev/null", "/usr/share/rhui-testing-tools/testing-data/bug916326", "root@rhua.example.com:/tmp/"])

        '''[TCMS#248534 setup] Change SELinux context'''
        Expect.ping_pong(self.rs.Instances["RHUA"][0], "chcon -R unconfined_u:object_r:httpd_sys_rw_content_t:s0 /tmp/bug916326/ && echo SUCCESS", "[^ ]SUCCESS")

    def _test(self):
        '''[TCMS#248534 test] Creating two pulp repos with nearly the same package '''
        Expect.ping_pong(self.rs.Instances["RHUA"][0], "pulp-admin -u admin -p admin repo create --id rh-repo --name rh-repo --feed file:///tmp/bug916326/rh-repo --relativepath=rh-repo && echo SUCCESS", "[^ ]SUCCESS", 10)

        Expect.ping_pong(self.rs.Instances["RHUA"][0], "pulp-admin -u admin -p admin repo sync --id rh-repo -F && echo SUCCESS", "[^ ]SUCCESS", 10)

        Expect.ping_pong(self.rs.Instances["RHUA"][0], "pulp-admin -u admin -p admin repo clone --id rh-repo --clone_id=rh-repo-clone -F && echo SUCCESS", "[^ ]SUCCESS", 10)

        Expect.ping_pong(self.rs.Instances["RHUA"][0], "pulp-admin -u admin -p admin repo create --id brew-repo --name brew-repo --feed file:///tmp/bug916326/brew-repo --relativepath=brew-repo && echo SUCCESS", "[^ ]SUCCESS", 10)
        
        Expect.ping_pong(self.rs.Instances["RHUA"][0], "pulp-admin -u admin -p admin repo sync --id brew-repo -F && echo SUCCESS", "[^ ]SUCCESS", 10)

        Expect.ping_pong(self.rs.Instances["RHUA"][0], "pulp-admin -u admin -p admin repo sync --id rh-repo-clone -F && echo SUCCESS", "[^ ]SUCCESS", 10)

    def _cleanup(self):
        '''[TCMS#248534 cleanup] Remove pulp repos '''
        for repo in ["rh-repo", "brew-repo", "rh-repo-clone"]:
            Expect.ping_pong(self.rs.Instances["RHUA"][0], "pulp-admin -u admin -p admin repo delete --id " + repo + " && echo SUCCESS", "[^ ]SUCCESS", 10)

if __name__ == "__main__":
    nose.run(defaultTest=__name__, argv=[__file__, '-v'])
