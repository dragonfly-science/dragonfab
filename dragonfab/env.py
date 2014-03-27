import sys
import os
import time

from fabric.api import local, env
#from fabric.operations import require
from fabric.tasks import Task

from importlib import import_module

from dragonfab import _lxc_remove

__all__ = []


# environments.py looks like:
#
# environments = {
#    'production': {
#         'hosts': ['app.example.com'],
#         'debconf': 'debconf.dat.production',
#         }
#    'lxc': {
#         'lxc': 'example-lxc',
#         'debconf': 'debconf.dat.lxc',
#         }
#
#    ...
# }
try:
    environments = import_module('environments')
except ImportError, e:
    print "Error importing environments module: '%s'" % str(e)
    sys.exit(1)


def get_lxc_dhcp_lease(lxc_name):
    result = local(
            "cat /var/lib/misc/dnsmasq.leases | grep ' %s ' | awk '{print $2, $3}'"
            % lxc_name, capture=True)
    if result:
        mac_addr, ip_addr = result.split()
        return mac_addr, ip_addr
    else:
        return None, None


# Template task for LXC environment
def _lxc(env_name, force_new=False):
    """ Ensure that we have an lxc, and set up hosts to point at it. """
    # Get and set up an lxc environment.
    lxc_env = environments.environments[env_name]
    lxc_name = lxc_env['lxc']
    if force_new or not os.path.exists('/var/lib/lxc/%s' % lxc_name):
        if 'lxc_template' in lxc_env:
            _new_lxc(lxc_name, template=lxc_env['lxc_template'])
        else:
            _new_lxc(lxc_name)

    # ensure that it is running
    status = local("sudo lxc-info -n %s" % lxc_name, capture=True)
    if 'STOPPED' in status:
        local("sudo lxc-start -n %s -d" % lxc_name)
        time.sleep(10) # give lxc time to start

    ip_address = local(
            "cat /var/lib/misc/dnsmasq.leases | grep ' %s ' | awk '{print $3}'"
            % lxc_name, capture=True)
    env.hosts = [ip_address]
    print "LXC setup on: %s" % ip_address


# __all__ is for shared values across environments
default_label = '__all__'
_defaults = environments.environments.get(default_label, {})


# For each environment we create a fabric task that will modify the fabric global env
for env_name, settings in environments.environments.iteritems():
    if env_name == default_label:
        continue
    if 'lxc' in settings:
        # lxc environments require special handling based off of the _lxc method
        class _lxc_task(Task):
            name = env_name
            env_settings = dict(settings)
            def run(self, force_new=None):
                env.update(_defaults)
                env.update(self.env_settings)
                env.env_name = self.name
                _lxc(self.name, force_new)
        t = _lxc_task()
        t.__doc__ = "Activate %s environment (lxc: '%s')." % (env_name, settings['lxc'])
        setattr(sys.modules[__name__], env_name, t)
    else:
        # most environments just update the fabric env variable
        class _set_env(Task):
            name = env_name
            env_settings = dict(settings)
            def run(self):
                env.update(_defaults)
                env.update(self.env_settings)
                env.env_name = env_name
        t = _set_env()
        t.__doc__ = "Activate %s environment." % env_name
        setattr(sys.modules[__name__], env_name, t)
    __all__.append(env_name)


def _new_lxc(lxc_name, template='vanilla'):
    """ Create a new LXC instance on the local machine. """
    old_dhcp_lease = get_lxc_dhcp_lease(lxc_name)
    if os.path.exists('/var/lib/lxc/%s' % lxc_name):
        _lxc_remove()
    if not os.path.exists('/var/lib/lxc/%s' % template):
        raise Exception("Error: you don't have a LXC to clone, called %s" % template)
    local("sudo lxc-clone -o %s -n %s" % (template, lxc_name))
    local("sudo lxc-start -n %s -d" % lxc_name)

    while old_dhcp_lease == get_lxc_dhcp_lease(lxc_name):
        # This is a hack to wait for the LXC to boot
        # lxc-wait, lxc-monitor and all the other lxc tools seem next to useless
        # if you want block until an lxc has finished booting
        time.sleep(10)
