import os
import time

from fabric.api import local, env, task, sudo, lcd, execute, put, require, run


# collectstatic specifically for deb build stage
# relies
# TODO: abstract out manage.py for use with other django commands
def _collectstatic():
    require('django_project', 'django_python')

    manage = os.path.join(env.django_project, 'manage.py')
    if not os.path.exists(manage):
        raise Exception('%s does not exist' % manage)

    django_python = env.django_python
    if not os.path.exists(django_python):
        raise Exception('%s does not exist' % django_python)

    local("%(python)s %(manage)s collectstatic --noinput"
          % {'python': django_python, 'manage': manage})


# Debian package controls
@task
def build():
    """ Build debian package. """
    require('package_name')
    # collect static files
    if 'wheel' in env and env.wheel:
        pip_build_dir = "/tmp/pip_build_%s_%s" % (env.user, env.package_name)
        if 'pip_build_dir' in env:
            pip_build_dir = env.pip_build_dir
        if os.path.isdir(pip_build_dir):
            local('rm -rf "%s"' % pip_build_dir)
        with lcd(env.local_dir):
            local('rm -rf wheelhouse')
            local("pip wheel -b %s -r requirements.txt" % pip_build_dir)
    if 'collectstatic' in env and env.collectstatic:
        _collectstatic()
    # clean out compiled python files
    local("find . -name \"*.pyc\" -exec rm {} \;")
    local("dpkg-buildpackage -rfakeroot -us -uc -b -tc -i\*.un\~ -i\*.swp")
    time.sleep(2)

def _latest_deb(package_name, package_dir):
    return local("(cd %(package_dir)s; ls -tr %(package_name)s*.deb) | tail -n1" % locals(), capture=True)

def _put_deb():
    """ Copy debian package on host. """
    with lcd(env.package_dir):
        put(env.debfile)

def _get_gdebi():
    """ Get gdebi version that actually works
    
    This bug in 12.04 breaks exit code expectations:
    https://bugs.launchpad.net/ubuntu/+source/gdebi/+bug/1033631
    """
    sudo("apt-get -qq install -yf gdebi-core")
    details = run('dpkg -s gdebi-core')
    buggy_version = '0.8.5build1'
    if 'Version: ' + buggy_version in details:
        sudo("apt-get -qq install -yf wget")
        run('wget https://launchpad.net/ubuntu/+archive/primary/+files/gdebi-core_0.8.5ubuntu1.1_all.deb')
        sudo('sudo gdebi -q --non-interactive gdebi-core_0.8.5ubuntu1.1_all.deb')

def _install_deb():
    """ Install package on host. """
    sudo("apt-get -qq update")
    _get_gdebi()
    if 'debconf' in env:
        if os.path.exists(env.debconf):
            put(env.debconf, '/root/debconf.dat', use_sudo=True)
            sudo("""DEBIAN_FRONTEND=noninteractive \
                  DEBCONF_DB_OVERRIDE='File{/root/debconf.dat}' \
                  gdebi -o Dpkg::Options::="--force-confnew" \
                  -q --non-interactive  %(debfile)s""" % env)
        else:
            # If debconf is defined but missing, treat as an error
            raise Exception('%s missing!' % env.debconf)
    else:
        sudo("gdebi -q %(debfile)s" % env)

@task
def deploy():
    """ Copy and install package on host. """
    require('package_name')
    if 'package_dir' not in env:
        env.package_dir = os.path.join(env.local_dir, '..')
    env.debfile = _latest_deb(env.package_name, env.package_dir)
    _put_deb()
    if 'wheel' in env and env.wheel:
        # ensure we have the the right versions of all the tools we need
        sudo("pip install -U 'pip>=1.4' wheel 'setuptools>=0.8'")
    _install_deb()
