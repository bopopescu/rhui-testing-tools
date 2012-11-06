#! /usr/bin/python -tt

from paramiko import SSHClient, AutoAddPolicy
import argparse
import sys
import time
import tempfile
import logging
import os
import random
import string
import yaml


class Instance(SSHClient):
    '''
    Instance to run commands via ssh
    '''
    def __init__(self, hostname, private_ip, public_ip):
        SSHClient.__init__(self)
        self.hostname = hostname
        self.public_ip = public_ip
        self.private_ip = private_ip
        self.load_system_host_keys()
        self.set_missing_host_key_policy(AutoAddPolicy())
        self.connect(hostname=hostname, username="root")
        self.sftp = self.open_sftp()
        self.ephemeral_device = None
        for device in self.run_sync("ls -1 /dev/xvd*").strip().split('\n'):
            # searching for the first unused block device
            if self.run_sync("grep " + device + " /proc/mounts").strip() == "":
                self.ephemeral_device = device
                logger.debug("Using " + device + " as additional storage")
                self.run_sync("mkfs.ext3 " + device, True)
                break

    def __repr__(self):
        return (self.__class__.__name__ + ":" + self.hostname + ":" + self.public_ip + ":" + self.private_ip)

    def run_sync(self, command, required=False):
        stdin, stdout, stderr = self.exec_command(command)
        output = stdout.read()
        logger.debug("Executing: '" + command + "' on " + self.hostname)
        status = stdout.channel.recv_exit_status()
        logger.debug("STDOUT: " + output)
        logger.debug("STDERR: " + stderr.read())
        logger.debug("STATUS: " + str(status))
        if required and status != 0:
            logger.error("Command " + command + " execution failed, exiting")
            sys.exit(1)
        stdin.close()
        stdout.close()
        stderr.close()
        return output


class RHUI_Instance(Instance):
    '''
    Class to represent RHUI instance (RHUA or CDS)
    '''
    def __init__(self, hostname, private_ip, public_ip, iso):
        Instance.__init__(self, hostname, private_ip, public_ip)
        self.iso = iso
        self.version = "1.0"

    def setup(self):
        logger.info("Common RHUI instance setup for " + self.hostname)
        remote_iso = "/root/" + os.path.basename(self.iso)
        logger.debug("Will mount " + self.iso + " to /mnt")
        self.run_sync("umount /mnt")
        self.sftp.put(self.iso, remote_iso)
        self.run_sync("mount -o loop " + remote_iso + " /mnt", True)
        # Setting up iptables
        logger.debug("Will allow tcp connection to ports 5674, 443")
        self.run_sync("iptables -I INPUT -p tcp --destination-port 443 -j ACCEPT", True)
        self.run_sync("iptables -I INPUT -p tcp --destination-port 5674 -j ACCEPT", True)
        self.run_sync("service iptables save", True)

    def set_confrpm_name(self, name):
        if name[-1:] == "\n":
            name = name[:-1]
        logger.debug("Setting up conf rpm name to " + name + " for " + self.hostname)
        self.confrpm = name

    def ephemeral_mount(self, mountpoint):
        if self.ephemeral_device:
            self.run_sync("mkdir " + mountpoint + " ||:", True)
            self.run_sync("chmod 755 " + mountpoint, True)
            self.run_sync("mount " + self.ephemeral_device + " " + mountpoint, True)
            self.run_sync("echo " + self.ephemeral_device + "\t" + mountpoint + "\text3\tdefaults\t0 0 >> /etc/fstab", True)


class RHUA(RHUI_Instance):
    '''
    Class to represent RHUA instance
    '''
    def setup(self, cds_list):
        logger.info("Setting up RHUA instance " + self.hostname)
        answersfile = tempfile.NamedTemporaryFile(delete=False)
        capassword = ''.join(random.choice(string.ascii_lowercase) for x in range(10))
        RHUI_Instance.setup(self)
        self.ephemeral_mount("/var/lib/pulp")
        logger.debug("Running /mnt/install_RHUA.sh")
        self.run_sync("cd /mnt && ./install_RHUA.sh", True)
        self.run_sync("chown apache.apache /var/lib/pulp", True)
        self.run_sync("mkdir /etc/rhui/pem ||:", True)
        self.run_sync("mkdir /etc/rhui/confrpm ||:", True)
        # Creating CA
        logger.debug("Creating CA")
        self.run_sync("echo " + capassword + " > /etc/rhui/pem/ca.pwd", True)
        self.run_sync("echo 10 > /etc/rhui/pem/ca.srl", True)
        self.run_sync("openssl req  -new -x509 -extensions v3_ca -keyout /etc/rhui/pem/ca.key -subj \"/C=US/ST=NC/L=Raleigh/CN=" + self.hostname + " CA\" -out /etc/rhui/pem/ca.crt -days 365 -passout \"pass:" + capassword + "\"", True)
        # Creating answers file
        logger.debug("Creating answers file " + answersfile.name)
        answersfile.write("[general]\n")
        answersfile.write("version: " + self.version + "\n")
        answersfile.write("dest_dir: /etc/rhui/confrpm\n")
        answersfile.write("qpid_ca: /etc/rhui/qpid/ca.crt\n")
        answersfile.write("qpid_client: /etc/rhui/qpid/client.crt\n")
        answersfile.write("qpid_nss_db: /etc/rhui/qpid/nss\n")
        for server in [self] + cds_list:
            # Creating server certs for RHUA and CDSs
            logger.debug("Creating cert for " + server.hostname)
            self.run_sync("openssl genrsa -out /etc/rhui/pem/" + server.hostname + ".key 2048", True)
            self.run_sync("openssl req -new -key /etc/rhui/pem/" + server.hostname + ".key -subj \"/C=US/ST=NC/L=Raleigh/CN=" + server.hostname + "\" -out /etc/rhui/pem/" + server.hostname + ".csr", True)
            self.run_sync("openssl x509 -req -days 365 -CA /etc/rhui/pem/ca.crt -CAkey /etc/rhui/pem/ca.key -passin \"pass:" + capassword + "\" -in /etc/rhui/pem/" + server.hostname + ".csr -out /etc/rhui/pem/" + server.hostname + ".crt", True)
            logger.debug("Adding " + server.hostname + " to answers")
            if server.__class__ == RHUA:
                answersfile.write("[rhua]\n")
            else:
                answersfile.write("[" + server.hostname + "]\n")
            answersfile.write("hostname: " + server.hostname + "\n")
            answersfile.write("rpm_name: " + server.hostname + "\n")
            answersfile.write("ssl_cert: /etc/rhui/pem/" + server.hostname + ".crt\n")
            answersfile.write("ssl_key: /etc/rhui/pem/" + server.hostname + ".key\n")
            answersfile.write("ca_cert: /etc/rhui/pem/ca.crt\n")
        answersfile.close()
        # Creating configuration RPMs
        logger.debug("Putting answers to /etc/rhui/answers on " + server.hostname)
        self.sftp.put(answersfile.name, "/etc/rhui/answers")
        logger.debug("Running rhui-installer")
        self.run_sync("rhui-installer /etc/rhui/answers", True)
        for server in [self] + cds_list:
            #Setting conf RPM names
            rpmname = self.run_sync("ls -1 /etc/rhui/confrpm/" + server.hostname + "-" + self.version + "-*.rpm | head -1")
            server.set_confrpm_name(rpmname)
        # Installing RHUA
        logger.debug("Installing RHUI conf rpm")
        self.run_sync("rpm -e " + self.hostname)
        self.run_sync("rpm -i " + self.confrpm, True)
        logger.info("RHUA " + self.hostname + " setup finished")


class CDS(RHUI_Instance):
    '''
    Class to represent CDS instance
    '''
    def setup(self, rhua):
        logger.info("Setting up CDS instance " + self.hostname + " associated with RHUA " + rhua.hostname)
        RHUI_Instance.setup(self)
        self.ephemeral_mount("/var/lib/pulp-cds")
        self.run_sync("cd /mnt && ./install_CDS.sh", True)
        self.run_sync("chown apache.apache /var/lib/pulp-cds", True)
        rpmfile = tempfile.NamedTemporaryFile(delete=False)
        rpmfile.close()
        logger.debug("will transfer " + self.confrpm + " from RHUA to " + rpmfile.name)
        rhua.sftp.get(self.confrpm, rpmfile.name)
        logger.debug("will transfer " + rpmfile.name + " to CDS " + rpmfile.name)
        self.sftp.put(rpmfile.name, rpmfile.name)
        logger.debug("will install " + rpmfile.name + " on CDS")
        self.run_sync("rpm -i " + rpmfile.name)
        logger.info("CDS " + self.hostname + " setup finished")


class CLI(Instance):
    '''
    Class to represent CLI instance
    '''
    def setup(self, rhua):
        pass


argparser = argparse.ArgumentParser(description='Create RHUI install')
argparser.add_argument('--debug', action='store_const', const=True,
                       default=False, help='debug output to the console (in addition to /var/log/rhui-installer.log)')
argparser.add_argument('--iso', required=True,
                       help='use supplied ISO file')
argparser.add_argument('--yamlfile',
                       default="/etc/rhui-testing.yaml", help='use specified YAML config file')
args = argparser.parse_args()

ISONAME = args.iso

if args.debug:
    loglevel = logging.DEBUG
else:
    loglevel = logging.INFO

logger = logging.getLogger('rhui_installer')
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler('/var/log/rhui-installer.log')
fh.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(loglevel)
formatter = logging.Formatter(fmt='%(asctime)s %(levelname)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
ch.setFormatter(formatter)
fh.setFormatter(formatter)
plogger = logging.getLogger("paramiko")
plogger.setLevel(logging.DEBUG)
plogger.addHandler(fh)
logger.addHandler(ch)
logger.addHandler(fh)

rhua = []
cds = []
cli = []
try:
    fd = open(args.yamlfile, "r")
    yamlconfig = yaml.load(fd)
    for instance in yamlconfig['Instances']:
        if instance['role'].upper() == "RHUA":
            logger.info("Adding RHUA instance " + instance['hostname'])
            instance = RHUA(instance['hostname'], instance['public_ip'], instance['private_ip'], args.iso)
            rhua.append(instance)
        elif instance['role'].upper() == "CDS":
            logger.info("Adding CDS instance " + instance['hostname'])
            instance = CDS(instance['hostname'], instance['public_ip'], instance['private_ip'], args.iso)
            cds.append(instance)
        elif instance['role'].upper() == "CLI":
            logger.info("Adding CLI instance " + instance['hostname'])
            instance = CLI(instance['hostname'], instance['public_ip'], instance['private_ip'])
            cli.append(instance)
        elif instance['role'].upper() == "MASTER":
            logger.debug("Skipping master node " + instance['hostname'])
        else:
            logger.info("host with unknown role " + instance['role'] + " " + instance['hostname'] + ", skipping")
    fd.close()
except Exception, e:
    logger.error("Failed to parse config file " + args.yamlfile +
                  " " + str(e.__class__) + ': ' + str(e))
    sys.exit(1)
logger.debug("RHUA: " + repr(rhua))
logger.debug("CDSs: " + repr(cds))
logger.debug("CLIs: " + repr(cli))

if len(rhua) > 1:
    logger.error("Don't know how to install RHUI with two or more RHUAs, exiting")
    sys.exit(1)
elif len(rhua) == 0:
    logger.error("Don't know how to install RHUI without RHUA, exiting")
    sys.exit(1)

if len(cds) == 0:
    logger.info("No CDSs found, will do only RHUA setup")

if len(cli) == 0:
    logger.info("No CLIs found")

rhua[0].setup(cds)
for cds_instance in cds:
    cds_instance.setup(rhua[0])
