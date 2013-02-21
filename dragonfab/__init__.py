import os

from fabric import api

if api.env.DEBUG:
    import logging
    logging.basicConfig(level=logging.DEBUG)

@api.task
def lxc_remove():
    """ Completely remove an existing LXC instance. """
    assert 'lxc' in api.env
    _lxc_remove()

def _lxc_remove():
    # Needed by dragonfab.env but we don't want multiple tasks to show up
    if os.path.exists('/var/lib/lxc/%(lxc)s' % api.env):
        api.local("sudo lxc-stop -n %(lxc)s" % api.env)
        api.local("sudo lxc-destroy -n %(lxc)s" % api.env)
