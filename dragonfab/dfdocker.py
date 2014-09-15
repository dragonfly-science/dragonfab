import json
import requests
import docker

from fabric.api import env, task, abort

def inspect_by_name(client, name):
    for container in client.containers(all=True):
        if name in [n[1:] for n in container['Names']]:
            return client.inspect_container(container['Id'])

def fetch_image(client, c):
    proto = c['registry'].split('://')[0]
    insecure_registry = proto == 'http'
    imagename = c['image'].split('/', 1)[1]
    url = c['registry'] + 'v1/search?q=' + imagename

    r = requests.get(url)
    if r.status_code != 200:
        abort("%s: status %d" % (url, r.status_code))

    result = json.loads(r.text)
    results = [i for i in result['results'] if imagename == i['name']]

    if len(results) > 1:
        abort("%s returned %d results" % (url, len(results)))

    if len(results) == 0:
        if 'build' not in cf:
            abort("No path to build image %s" % imagename)
        client.build(c['build'])
        client.push(c['image'], insecure_registry=insecure_registry)
    elif len(results) == 1:
        client.pull(c['image'], insecure_registry=insecure_registry)

def initialise_container(client, c):
    status = inspect_by_name(client, c['name'])

    if not client.images(c['name']):
        fetch_image(client, c)

    if not status:
        ports = c.get('ports', None)
        client.create_container(c['image'], name=c['name'], ports=ports)
        status = inspect_by_name(client, c['name'])

    print("%s:%s" % (c['name'], status['Id'][0:12]))

    if not status['State']['Running'] and c.get('start', True):
        volumes_from = c.get('volumes_from', None)
        binds = c.get('binds', None)
        port_bindings = c.get('port_bindings', None)
        links = c.get('links', None)
        client.start(
            status['Id'], volumes_from=volumes_from, binds=binds,
            port_bindings=port_bindings, links=links)

@task
def setup_containers():
    #TODO remote connections
    base_url = 'unix://var/run/docker.sock'
    client = docker.Client(base_url)
    for c in env.containers:
        initialise_container(client, c)
