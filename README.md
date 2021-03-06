RHUI testing tools
==================

Contents:
--------
Scripts (scripts/, placed under /usr/bin in rpm):

   * `create-cf-stack.py` - to create CloudForamtion stack of resources (cnf/ contains examples)
   * `remote-rhui-installer.sh` - to run remote RHUI installer
   * `rhui-installer.py` - RHUI installer (must be run on 'Master' node)

RHUI tests (rhui-tests/, placed under /usr/share/rhui-testing-tools/rhui-tests in rpm):

   * `test-rhui-workflow-simple.py` - simple workflow (basic test)

Requirements for running:
------------------------
You need to install python modules and rhui-testing-tools before using them:

1. In case you dont have it, install PIP tool: `sudo yum install python-pip`
2. Install boto (aws python interface): `pip install boto`
3. Install Python Yaml support: `sudo yum install PyYAML`
4. Install rhui-testing-tools - run in directory where this README is placed: `sudo python setup.py install`

Basic usage:
-----------
1. Create cloudformation stack for testing:
    * without rpm: `scripts/create-cf-stack.py  --region eu-west-1`
    * with rpm installed: `create-cf-stack.py --region eu-west-1`

    Mind parameters to specify required configuration: `--rhel5 --rhel6 --rhel7 --cds --proxy`

    Default configuration: 1xRHEL6, 1xCDs
    
    **NOTE**: In case it is your first time using EC2 cloud, you need to create key chain pair in webui of AWS:
    * Go to AWS webui, select your region and on dashboard page choose "Key Pairs"
    * There select Create Key Pair - you will be asked for name and than you will be offered a download of pem file.
    * You will need this name and path to this file changed in `rhui_ec2.yaml`.

    `/etc/rhui_ec2.yaml` is used as config file. Change `ec2-key` and `ec2-secret-key` values to your keys. An example:
    ```
    ec2: {ec2-key: AAAAAAAAAAAAAAAAAAAA, ec2-secret-key: B0B0B0B0B0B0B0B0B0B0a1a1a1a1a1a1a1a1a1a1}
    ssh:
      ap-northeast-1: [user-ap-northeast-1, /home/user/.pem/ap-northeast-1-iam.pem]
      ap-southeast-1: [user-ap-southeast-1, /home/user/.pem/ap-southeast-1-iam.pem]
      ap-southeast-2: [user-ap-southeast-2, /home/user/.pem/ap-southeast-2-iam.pem]
      eu-west-1: [user-eu-west-1, /home/user/.pem/eu-west-1-iam.pem]
      sa-east-1: [user-sa-east-1, /home/user/.pem/sa-east-1-iam.pem]
      us-east-1: [user-us-east-1, /home/user/.pem/us-east-1-iam.pem]
      us-west-1: [user-us-west-1, /home/user/.pem/us-west-1-iam.pem]
      us-west-2: [user-us-west-2, /home/user/.pem/us-west-2-iam.pem]
    ```

2. Build actual rhui-testing-tools package (if you have no) using 'tito' tool: `tito build --rpm --test`

3. Run remote rhui installer:

    * without rpm: `scripts/remote-rhui-installer.sh <master ip> <your-region-ssh-key> <RHUI iso> <rhui-testing-tools.rpm>`
    * with rpm installed: `remote-rhui-installer.sh <master ip> <your-region-ssh-key> <RHUI iso> <rhui-testing-tools.rpm>`

    You can get rhui-testing-tools RPM [here](https://rhuiqerpm.s3.amazonaws.com/index.html).

4. Add rh entitlement certificate and (optionally) rh-sighned RPM with `scripts/remote-add-rh-cert.sh` and `scripts/remote-add-rh-rpm.sh` scripts

5. Go to master `ssh -i <your-region-ssh-key> <master ip>`

6. Run simple workflow `python /usr/share/rhui-testing-tools/rhui-tests/test_rhui_workflow_simple.py`

7. You can run a whole testplan: `cd /usr/share/rhui-testing-tools/testplans/tcms6606/ && nosetests -vv`


To send results to TCMS:
-----------------------
1. run testplan with `--with-xunit` option

2. Scp `nosetests.xml` file to the local host and run script to report the result: `./nitrate-test-result.py -p <testplan ID>  result_file`


To do test coverage:
-------------------
1. When creating a new stack add `--coverage` option to `remote-rhui-installer.sh`

2. Run tesplans

3. After that perform following steps:

   * on Master `scp .ssh/id_rsa rhua.example.com:.ssh/`
   * on RHUA
```
    rpm -e python-moncov
    scp -r cds1.example.com:/usr/lib/python2.6/site-packages/pulp/cds /usr/lib/python2.6/site-packages/pulp/
    scp -r cds1.example.com:/srv/pulp/cds.wsgi /srv/pulp/
    mkdir html
    coverage html -i --include="/usr/bin/rhui-manager,/usr/bin/rhui_configurator,/usr/lib/python2.6/site-packages/rhui/*" -d html/rhui-tools/ ; coverage html -i --include="/usr/bin/goferd,/usr/lib/gofer/*,/usr/lib/python2.6/site-packages/gofer/*" -d html/gofer/ ; coverage html -i --include="/usr/lib/python2.6/site-packages/grinder/*" -d html/grinder/ ; coverage html -i --include="/srv/pulp/cds/*,/usr/bin/pulp-admin,/usr/bin/pulp-migrate,/usr/lib/python2.6/site-packages/pulp/*" -d html/pulp/
```
