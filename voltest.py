from novaclient.v1_1 import client
from time import sleep
from fabric.api import execute, env, local, run
from os.path import expanduser

import os
import sys



user = os.environ.get('OS_USERNAME')
tenant = os.environ.get('OS_TENANT_NAME')
auth_url = os.environ.get('OS_AUTH_URL')
password = os.environ.get('OS_PASSWORD')

testing_image = 'centos-6-20120921'

# TODO: Could make a new one each run and delete at the end
private_key = 'mxckey'

def update():
    run('yum update -y')

def pssh():
    run('yum install wget -y')
    run('wget http://apt.sw.be/redhat/el6/en/i386/rpmforge/RPMS/pssh-2.3-1.el6.rf.noarch.rpm')
    run('rpm -i pssh-2.3-1.el6.rf.noarch.rpm')

def inittest():
    run('pscp -h .hostlist -l root script /root/script')
    run('pscp -h .hostlist -l root script /root/initialise')
    run("pssh -h .hostlist -l root -t 0 -o /tmp -x '-o StrictHostKeyChecking=no' 'chmod ug+x /root/initialise'")
    run("pssh -h .hostlist -l root -t 0 -o /tmp -x '-o StrictHostKeyChecking=no' ./initialise")

def runtest():
    run("pssh -h .hostlist -l root -t 0 -o /tmp -x '-o StrictHostKeyChecking=no' ./script")


cl = client.Client(user, password, tenant, auth_url, service_type="compute", insecure=True)

# security group
sg = ['open']

for image in cl.images.list():
    if image.name == testing_image:
        basecentos = image
large = ''
for flavor in cl.flavors.list():
    if flavor.name == 'm1.large':
        large = flavor

num_servers = 3

for i in range(num_servers):
    name = "voltest" + str(i)
    image = basecentos
    flavor = large

    # other vms to avoid
    ids  = [s.id for s in cl.servers.list()]
    hints = dict()
    hints['different_host'] = ids

    current_servers = [s.name for s in cl.servers.list() if s.status == u'ACTIVE']
    if name not in current_servers:
        cl.servers.create(name, image, flavor, key_name=private_key, scheduler_hints=hints, security_groups=sg)

    # not safe due to ERROR state!
    while name not in current_servers:
        sleep(2)
        print "current servers: " + str(current_servers)
        current_servers = [s.name for s in cl.servers.list() if s.status == u'ACTIVE']

# add a public IP to one of the VMs to use as a gateway
current_servers = [s for s in cl.servers.list() if (s.status == u'ACTIVE' and 'voltest' in s.name)]
floating_pool = cl.floating_ip_pools.list()[0]
floating_ips = cl.floating_ips.list()

free_ips = [ip for ip in cl.floating_ips.list() if ip.instance_id == None]

if not free_ips:
    print "No free IP addresses to associate with head node"
    sys.exit()
     
head_node_ip = free_ips[0]
current_servers[0].add_floating_ip(head_node_ip)

# TODO replace this with some sort of check to see that the floating IP is responding
# perhaps open port 22 or something similar
def check_floating_ip():
    for ip in cl.floating_ips.list():
        if ip.ip == head_node_ip.ip and ip.instance_id:
            return True
    return False        

while not check_floating_ip():
    print "waiting for floating ip"
    sleep(1)

# get rid of known hosts entry so Fabric doesn't complain
with open(expanduser('~') + '/.ssh/known_hosts', 'r') as known_hosts:
    hosts = known_hosts.readlines()

with open(expanduser('~') + '/.ssh/known_hosts', 'w') as known_hosts:
    for host in hosts:
        if host.split(' ')[0] != head_node_ip.ip:
            known_hosts.write(host)

sleep(10)
# push private key out to head node so it can orchestrate
local('scp -i ' + private_key + '.private' + ' -o StrictHostKeyChecking=no ' + private_key + '.private ' + 'root@' + str(head_node_ip.ip) + ':/root' )

# create host list for pssh to use
with open('.hostlist', 'w+') as hostlist:
    for server in current_servers:
        hostlist.write(server.networks['private'][0] + '\n')

local('scp -i ' + private_key + '.private' + ' -o StrictHostKeyChecking=no ' +  '.hostlist ' + 'root@' + str(head_node_ip.ip) + ':/root' )
local('scp -i ' + private_key + '.private' + ' -o StrictHostKeyChecking=no ' +  'script ' + 'root@' + str(head_node_ip.ip) + ':/root' )

# Fabric environment settings
env.key_filename = private_key + '.private'
env.user = 'root'
env.host_string=str(head_node_ip.ip)

# update headnode and install pssh
execute(update, hosts=[str(head_node_ip.ip)])
execute(pssh, hosts=[str(head_node_ip.ip)])
execute(runtest, hosts=[str(head_node_ip.ip)])
execute(inittest, hosts=[str(head_node_ip.ip)])

local('scp -i ' + private_key + '.private' + '-r -o StrictHostKeyChecking=no ' +  'root@' + str(head_node_ip.ip) + ':/root/out ' + './results' )
