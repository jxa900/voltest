from novaclient.v1_1 import client
from time import sleep

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

num_servers = 8

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

    while name not in current_servers:
        sleep(2)
        print current_servers
        current_servers = [s.name for s in cl.servers.list() if s.status == u'ACTIVE']


