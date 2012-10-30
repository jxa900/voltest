from novaclient.v1_1 import client
from time import sleep
from fabric.api import execute, env, local, run
import os
import sys

user = os.environ.get('OS_USERNAME')
tenant = os.environ.get('OS_TENANT_NAME')
auth_url = os.environ.get('OS_AUTH_URL')
password = os.environ.get('OS_PASSWORD')

cl = client.Client(user, password, tenant, auth_url, service_type="compute", insecure=True)

servers  = cl.servers.list()

for s in servers:
    if 'voltest' in s.name:
        s.delete()

current_servers = [s.name for s in cl.servers.list() if s.status == u'ACTIVE']

while current_servers:
    sleep(1)
    print current_servers
    current_servers = [s.name for s in cl.servers.list() if s.status == u'ACTIVE']
