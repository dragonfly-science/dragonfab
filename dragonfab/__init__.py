import os

from fabric.api import local, env, task

if env.DEBUG:
    import logging
    logging.basicConfig(level=logging.DEBUG)

@task
def lxc_remove():
    """ Completely remove an existing LXC instance. """
    assert 'lxc' in env
    _lxc_remove()

def _lxc_remove():
    # Needed by dragonfab.env but we don't want multiple tasks to show up
    if os.path.exists('/var/lib/lxc/%(lxc)s' % env):
        local("sudo lxc-stop -n %(lxc)s" % env)
        local("sudo lxc-destroy -n %(lxc)s" % env)
