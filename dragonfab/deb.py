import os
import time

from fabric.api import local, env, task, sudo, lcd, execute, put, require


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

    deb_settings = 'deb_settings'
    if not os.path.exists(os.path.join(env.django_project, deb_settings + '.py')):
        raise Exception('%s does not exist' % os.path.join(env.django_project, deb_settings + '.py'))

    local("%(python)s %(manage)s collectstatic --noinput --settings=%(deb)s"
          % {'python':django_python, 'manage': manage, 'deb': deb_settings})


# Debian package controls
@task
def build():
    """ Build debian package. """
    # clean out compiled python files
    if 'collectstatic' in env and env.collectstatic:
        _collectstatic()
    local("find . -name \"*.pyc\" -exec rm {} \;")
    # This is the same as local("make package"), but doesn't require projects
    # have a Makefile
    local("dpkg-buildpackage -rfakeroot -us -uc -b -tc")
    time.sleep(2)

def _latest_deb(package_name, package_dir):
    return local("(cd %(package_dir)s; ls -tr %(package_name)s*.deb) | tail -n1" % locals(), capture=True)

def _put_deb():
    """ Copy debian package on host. """
    env.debfile = _latest_deb(env.package_name, env.package_dir)
    with lcd(env.package_dir):
        put(env.debfile)

def _install_deb():
    """ Install package on host. """
    env.debfile = _latest_deb(env.package_name, env.package_dir)
    sudo("apt-get -qq update")
    sudo("apt-get -qq install -yf gdebi-core")
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
    assert 'package_name' in env, "Define Debian package name as env.package_name"
    if 'package_dir' not in env:
        env.package_dir = os.path.join(env.local_dir, '..')
    execute(_put_deb)
    execute(_install_deb)

