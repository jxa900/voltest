from novaclient.v1_1 import client
from time import sleep
from fabric.tasks import execute

import os
import sys

user = os.environ.get('OS_USERNAME')
tenant = os.environ.get('OS_TENANT_NAME')
auth_url = os.environ.get('OS_AUTH_URL')
password = os.environ.get('OS_PASSWORD')

cl = client.Client(user, password, tenant, auth_url, service_type="compute", insecure=True)

servers = cl.servers.list()

sg = ['open']
ids  = [s.id for s in servers]

for image in cl.images.list():
    if image.name == 'centos-6-20120921':
        basecentos = image
large = ''
for flavor in cl.flavors.list():
    if flavor.name == 'm1.large':
        large = flavor

num_servers = 0

for i in range(num_servers):
    name = "voltest" + str(i)
    image = basecentos
    flavor = large

    # other vms to avoid
    ids  = [s.id for s in cl.servers.list()]
    hints = dict()
    hints['different_host'] = ids

    cl.servers.create(name, image, flavor, key_name='mxckey', scheduler_hints=hints, security_groups=sg)

    current_servers = [s.name for s in cl.servers.list() if s.status == u'ACTIVE']

    # not safe due to ERROR state!
    while name not in current_servers:
        sleep(2)
        print current_servers
        current_servers = [s.name for s in cl.servers.list() if s.status == u'ACTIVE']

# add a public IP to one of the VMs to use as a gateway
current_servers = [s for s in cl.servers.list() if (s.status == u'ACTIVE' and 'voltest' in s.name)]
print current_servers
floating_pool = cl.floating_ip_pools.list()[0]
floating_ips = cl.floating_ips.list()

free_ips = [ip for ip in cl.floating_ips.list() if ip.instance_id == None]
print free_ips

# if all our current IPs are being used, try to create a new one?
# maybe just let it be...
if not free_ips:
    print "No free IP addresses to associate with head node"
    sys.exit()
     
head_node_ip = free_ips[0]
current_servers[0].add_floating_ip(head_node_ip)

# installing pssh and whatnot
#execute('yum update', hosts=[''])

