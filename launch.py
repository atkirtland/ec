from datetime import datetime
import time
import subprocess
import os
import json
import sys

def user():
    import getpass
    return getpass.getuser()

def launch(size = "t2.micro", name = ""):
    # aws ec2 run-instances --image-id ami-835f6ae6 --instance-type "t2.micro" --key-name testing --associate-public-ip-address
    o = json.loads(subprocess.check_output(["aws","ec2","run-instances",
                                            "--image-id","ami-835f6ae6",
                                            "--instance-type",size,
                                            "--security-groups","publicssh",
                                            "--instance-initiated-shutdown-behavior","terminate",
                                            "--key-name","testing"]))
    instance = o[u"Instances"][0][u"InstanceId"]
    print "Launched instance", instance

    
    name = user() + name
    print "Naming instance",name
    os.system("aws ec2 create-tags --resources %s --tags Key=Name,Value=%s"%(instance,
                                                                             name))
    
    o = json.loads(subprocess.check_output(["aws","ec2","describe-instances",
                                            "--instance-ids",instance]))
    address = o[u'Reservations'][0][u'Instances'][0][u'PublicIpAddress']
    print "Retrieved IP address of instance %s; got %s"%(instance,address)
    return instance, address


def sendCommand(address, script, job_id, upload, tar, shutdown):
    import tempfile
    preamble = """#!/bin/bash
cd ~/ec
git pull
git apply patch
mkdir jobs
"""
    if upload:
        # This is probably a terribly insecure idea...
        # But I'm not sure what the right way of doing it is
        # I'm just going to copy over the local SSH identity
        # Assuming that this is an authorized key at the upload site this will work
        # Of course it also means that if anyone were to pull the keys off of AWS,
        # they would then have access to every machine that you have access to
        UPLOADFREQUENCY = 60*3 # every 3 minutes
        if tar:
            uploadCommand = """\
tar czf {id}.tar.gz jobs experimentOutputs patch && \
scp -o StrictHostKeyChecking=no \
{id}.tar.gz {upload}""".format(id=job_id, upload=upload)
        else:
            uploadCommand = """\
rsync  -e 'ssh  -o StrictHostKeyChecking=no' -avz \
jobs experimentOutputs {}""".format(upload)
        preamble += """
chmod 600 ~/.ssh/id_rsa
chmod 600 ~/.ssh/id_rsa.pub
bash -c "while sleep %d
do %s
done" &
UPLOADPID=$!
"""%(UPLOADFREQUENCY, uploadCommand)
    
    script = preamble + script

    if upload:
        script += """
kill -9 $UPLOADPID
%s
"""%(uploadCommand)
    if shutdown:
        script += """
sudo shutdown -h now
"""

    fd = tempfile.NamedTemporaryFile(mode = 'w',delete = False,dir = "/tmp")
    fd.write(script)
    fd.close()
    name = fd.name

    print "SCRIPT:"
    print script

    # Copy over the script
    print "Copying script over to",address
    os.system("""
        scp -o StrictHostKeyChecking=no -i ~/.ssh/testing.pem \
            %s ubuntu@%s:~/script.sh""" % (name, address))

    # delete local copy
    os.system("rm %s"%name)

    # Send keys
    if upload:
        print "Uploading your ssh identity"
        os.system("""
            scp -o StrictHostKeyChecking=no -i ~/.ssh/testing.pem \
                ~/.ssh/id_rsa ~/.ssh/id_rsa.pub \
                ubuntu@%s:.ssh/"""%address)

    # Send git patch
    print "Sending git patch over to",address
    os.system("git diff --stat")
    os.system("""
        (echo "Base-Ref: $(git rev-parse HEAD)" ; echo ; git diff origin/master) | \
        ssh -o StrictHostKeyChecking=no -i ~/.ssh/testing.pem \
            ubuntu@{} 'cat > ~/ec/patch'
        """.format(address))

    # Execute the script
    # For some reason you need to pipe the output to /dev/null in order to get it to detach
    os.system("""
        ssh -o StrictHostKeyChecking=no -i ~/.ssh/testing.pem \
            ubuntu@{} 'bash ./script.sh > /dev/null 2>&1 &'
        """.format(address))
    print "Executing script on remote host."


def launchExperiment(name, command, upload=None, tar=False, shutdown=True, size="t2.micro"):
    job_id = "{}_{}_{}".format(name, user(), datetime.now().strftime("%FT%T"))
    if upload is None:
        if shutdown:
            print "You didn't specify an upload host, and also specify that the machine should shut down afterwards. These options are incompatible because this would mean that you couldn't get the experiment outputs."
            assert False
    script = """
%s > jobs/%s 2>&1
"""%(command, job_id)
    
    instance, address = launch(size, name=name)
    time.sleep(60)
    sendCommand(address, script, job_id, upload, tar, shutdown)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="")
    parser.add_argument('-u',"--upload",
                        default={
                            "ellisk": "ellisk@openmind7.mit.edu:/om2/user/ellisk/ec",
                            "lucasem": "lucasem@rig.lucasem.com:repo/ec",
                        }.get(user(), None))
    parser.add_argument('-z',"--size",
                        default="t2.micro")
    parser.add_argument('-k',"--shutdown",
                        default=False,
                        action="store_true")
    parser.add_argument('-t',"--tar",
                        default=False,
                        help="if uploading, this sends a single tarball with relevant outputs.",
                        action="store_true")
    parser.add_argument("name")
    parser.add_argument("command")
    arguments = parser.parse_args()

    launchExperiment(arguments.name,
                     arguments.command,
                     shutdown=arguments.shutdown,
                     size=arguments.size,
                     upload=arguments.upload,
                     tar=arguments.tar)

"""
BILLING: https://console.aws.amazon.com/billing/home?#/
Do not go over $10k
t2.nano	1	Variable	0.5	EBS Only	$0.0058 per Hour
t2.micro	1	Variable	1	EBS Only	$0.0116 per Hour
t2.small	1	Variable	2	EBS Only	$0.023 per Hour
t2.medium	2	Variable	4	EBS Only	$0.0464 per Hour
t2.large	2	Variable	8	EBS Only	$0.0928 per Hour
t2.xlarge	4	Variable	16	EBS Only	$0.1856 per Hour
t2.2xlarge	8	Variable	32	EBS Only	$0.3712 per Hour
m4.large	2	6.5	8	EBS Only	$0.1 per Hour
m4.xlarge	4	13	16	EBS Only	$0.2 per Hour
m4.2xlarge	8	26	32	EBS Only	$0.4 per Hour
m4.4xlarge	16	53.5	64	EBS Only	$0.8 per Hour
m4.10xlarge	40	124.5	160	EBS Only	$2 per Hour
m4.16xlarge	64	188	256	EBS Only	$3.2 per Hour
Compute Optimized - Current Generation
c4.large	2	8	3.75	EBS Only	$0.1 per Hour
c4.xlarge	4	16	7.5	EBS Only	$0.199 per Hour
c4.2xlarge	8	31	15	EBS Only	$0.398 per Hour
c4.4xlarge	16	62	30	EBS Only	$0.796 per Hour
c4.8xlarge	36	132	60	EBS Only	$1.591 per Hour
GPU Instances - Current Generation
p2.xlarge	4	12	61	EBS Only	$0.9 per Hour
p2.8xlarge	32	94	488	EBS Only	$7.2 per Hour
p2.16xlarge	64	188	732	EBS Only	$14.4 per Hour
p3.2xlarge	8	23.5	61	EBS Only	$3.06 per Hour
p3.8xlarge	32	94	244	EBS Only	$12.24 per Hour
p3.16xlarge	64	188	488	EBS Only	$24.48 per Hour
g3.4xlarge	16	47	122	EBS Only	$1.14 per Hour
g3.8xlarge	32	94	244	EBS Only	$2.28 per Hour
g3.16xlarge	64	188	488	EBS Only	$4.56 per Hour
Memory Optimized - Current Generation
x1.16xlarge	64	174.5	976	1 x 1920 SSD	$6.669 per Hour
x1.32xlarge	128	349	1952	2 x 1920 SSD	$13.338 per Hour
r3.large	2	6.5	15	1 x 32 SSD	$0.166 per Hour
r3.xlarge	4	13	30.5	1 x 80 SSD	$0.333 per Hour
r3.2xlarge	8	26	61	1 x 160 SSD	$0.665 per Hour
r3.4xlarge	16	52	122	1 x 320 SSD	$1.33 per Hour
r3.8xlarge	32	104	244	2 x 320 SSD	$2.66 per Hour
r4.large	2	7	15.25	EBS Only	$0.133 per Hour
r4.xlarge	4	13.5	30.5	EBS Only	$0.266 per Hour
r4.2xlarge	8	27	61	EBS Only	$0.532 per Hour
r4.4xlarge	16	53	122	EBS Only	$1.064 per Hour
r4.8xlarge	32	99	244	EBS Only	$2.128 per Hour
r4.16xlarge	64	195	488	EBS Only	$4.256 per Hour
Storage Optimized - Current Generation
i3.large	2	7	15.25	1 x 475 NVMe SSD	$0.156 per Hour
i3.xlarge	4	13	30.5	1 x 950 NVMe SSD	$0.312 per Hour
i3.2xlarge	8	27	61	1 x 1900 NVMe SSD	$0.624 per Hour
i3.4xlarge	16	53	122	2 x 1900 NVMe SSD	$1.248 per Hour
i3.8xlarge	32	99	244	4 x 1900 NVMe SSD	$2.496 per Hour
i3.16xlarge	64	200	488	8 x 1900 NVMe SSD	$4.992 per Hour
h1.2xlarge	8	26	32	1 x 2000 HDD	$0.55 per Hour
h1.4xlarge	16	53.5	64	2 x 2000 HDD	$1.1 per Hour
h1.8xlarge	32	99	128	4 x 2000 HDD	$2.2 per Hour
h1.16xlarge	64	188	256	8 x 2000 HDD	$4.4 per Hour
d2.xlarge	4	14	30.5	3 x 2000 HDD	$0.69 per Hour
d2.2xlarge	8	28	61	6 x 2000 HDD	$1.38 per Hour
d2.4xlarge	16	56	122	12 x 2000 HDD	$2.76 per Hour
d2.8xlarge	36	116	244	24 x 2000 HDD	$5.52 per Hour
"""