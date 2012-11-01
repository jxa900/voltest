from novaclient.v1_1 import client
from time import sleep
from fabric.api import execute, env, local, run
from os.path import expanduser
from socket import socket, AF_INET, SOCK_STREAM

import os
import sys



user = os.environ.get('OS_USERNAME')
tenant = os.environ.get('OS_TENANT_NAME')
auth_url = os.environ.get('OS_AUTH_URL')
password = os.environ.get('OS_PASSWORD')

testing_image = 'centos-6-20121101'

# TODO: Could make a new one each run and delete at the end
private_key = 'mxckey'

def update():
    run('yum update -y')

def pssh():
    run('yum install wget -y')
    run('wget http://apt.sw.be/redhat/el6/en/i386/rpmforge/RPMS/pssh-2.3-1.el6.rf.noarch.rpm')
    run('rpm -i pssh-2.3-1.el6.rf.noarch.rpm')
    run('wget http://pkgs.repoforge.org/iozone/iozone-3.394-1.el6.rf.x86_64.rpm')

def inittest():
    run("pscp -h .hostlist -l root -x '-o StrictHostKeyChecking=no' script /root/script")
    run("pscp -h .hostlist -l root -x '-o StrictHostKeyChecking=no' initialise /root/initialise")
    run("pscp -h .hostlist -l root -x '-o StrictHostKeyChecking=no' iozone-3.394-1.el6.rf.x86_64.rpm /root/iozone-3.394-1.el6.rf.x86_64.rpm")
    run("pssh -h .hostlist -l root -t 0 -o /tmp -x '-o StrictHostKeyChecking=no' 'chmod ug+x /root/initialise'")
    run("pssh -h .hostlist -l root -t 0 -o /tmp -x '-o StrictHostKeyChecking=no' ./initialise")
    run("mkdir -p /root/out")

def runtest():
    run("pssh -h .hostlist -l root -t 0 -o /root/out -x '-o StrictHostKeyChecking=no' ./script")


def test_port(ip, port, timeout=10):
    s = socket(AF_INET, SOCK_STREAM)
    s.settimeout(timeout)
    result = s.connect_ex((ip, port))
    s.close()
    if result == 0:
        return True
    else:
        return False

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
        if ip.ip == head_node_ip.ip and ip.instance_id == current_servers[0].id:
            return True
    return False        

while not check_floating_ip():
    print "waiting for floating ip"
    sleep(1)

# Give the head node 30 seconds to initialise its ssh port after booting
# before trying to log in
#if not test_port(head_node_ip.ip, 22, 30):
#    print "head node failed to respond in a timely manner"
#    sys.exit()

# get rid of known hosts entry so Fabric doesn't complain
with open(expanduser('~') + '/.ssh/known_hosts', 'r') as known_hosts:
    hosts = known_hosts.readlines()

with open(expanduser('~') + '/.ssh/known_hosts', 'w') as known_hosts:
    for host in hosts:
        if host.split(' ')[0] != head_node_ip.ip:
            known_hosts.write(host)

# push private key out to head node so it can orchestrate
local('scp -i ' + private_key + '.private' + ' -o StrictHostKeyChecking=no ' + private_key + '.private ' + 'root@' + str(head_node_ip.ip) + ':/root/.ssh/id_rsa' )

# create host list for pssh to use
with open('.hostlist', 'w+') as hostlist:
    for server in current_servers:
        hostlist.write(server.networks['private'][0] + '\n')

local('scp -i ' + private_key + '.private' + ' -o StrictHostKeyChecking=no ' +  '.hostlist ' + 'root@' + str(head_node_ip.ip) + ':/root' )
local('scp -i ' + private_key + '.private' + ' -o StrictHostKeyChecking=no ' +  'script ' + 'root@' + str(head_node_ip.ip) + ':/root' )
local('scp -i ' + private_key + '.private' + ' -o StrictHostKeyChecking=no ' +  'initialise ' + 'root@' + str(head_node_ip.ip) + ':/root' )

# Fabric environment settings
env.key_filename = private_key + '.private'
env.user = 'root'
env.host_string=str(head_node_ip.ip)

# update headnode and install pssh
execute(update, hosts=[str(head_node_ip.ip)])
execute(pssh, hosts=[str(head_node_ip.ip)])
execute(inittest, hosts=[str(head_node_ip.ip)])
execute(runtest, hosts=[str(head_node_ip.ip)])

local('scp -i ' + private_key + '.private ' + '-r -o StrictHostKeyChecking=no ' +  'root@' + str(head_node_ip.ip) + ':/root/out ' + './results' )
