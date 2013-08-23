import os

from fabric import api
from fabric.api import cd, sudo, local, run

# NOTE: These are not full proof, and will fail if there is any junk output due to
# login scripts (e.g. virtualenvwrapper first time setup).
remote_md5 = lambda f: run('md5sum %s' % f).split()[0]
local_md5 = lambda f: local('md5sum %s' % f, capture=True).split()[0]

if hasattr(api.env, 'DEBUG') and api.env.DEBUG:
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
        local("sudo lxc-stop -n %(lxc)s" % api.env)
        local("sudo lxc-destroy -n %(lxc)s" % api.env)

@api.task
def git_update(repo, path, user):
    """ Clone or update (if it already exists) a repo to path, chown to user """
    from fabric.contrib.files import exists
    if not exists(path):
        sudo('mkdir -p %s' % path)
    # Get the dirname from a git@... repo format string
    try:
        repo_name = repo.split('/')[-1].split('.')[0]
    except IndexError:
        raise Exception('Bad git repo string %s' % repo)
    repo_dir = os.path.join(path,repo_name)
    if not exists(repo_dir):
        with cd(path):
            sudo('git clone %s' % repo)
    else:
        with cd(repo_dir):
            sudo('git pull origin master')
    sudo('chown -R %s:%s' % (user, user))
    return repo_dir

@api.task
def apt_install(packages, update=True):
    if update:
        sudo('apt-get update')
    sudo('apt-get install -y ' + ' '.join(packages))

@api.task
def linkchecker(root_url, ignore_urls=[], ignore_warnings=False):
    cmd = 'linkchecker %s' % root_url
    for i in ignore_urls:
        cmd += ' --ignore-url %s' % i
    if ignore_warnings:
        cmd += ' --no-warnings'
    run(cmd)

