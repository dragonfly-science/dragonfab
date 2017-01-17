import os

from fabric.api import local, env, task, sudo, lcd, put, run, cd, settings, get, require, abort, execute
from fabric.contrib.files import exists

from dragonfab import local_md5, remote_md5

def _connection_string(env, dba=False):
    conn_str = ''
    options = [('-h', 'db_host'),
               ('-p', 'db_port'),
               ('', 'db_name')]
    if dba:
       options.append(('-U', 'dba'))
    else:
       options.append(('-U', 'db_user'))
    for param, val in options:
        if val in env and env.get(val):
            conn_str += ' %s %s' % (param, env.get(val))
    conn_str += ' '
    return conn_str

rdump_path = '/var/backups/dumps/latest.sql.gz'

@task
def dump():
    """ Copy current database from remote server to dumps/latest.sql.gz """
    require('local_dir')
    sudo('mkdir -p %s' % os.path.dirname(rdump_path))

    with lcd(env.local_dir):
        local('mkdir -p dumps')
        if os.path.exists('dumps/latest.sql.gz'):
            local('mv dumps/latest.sql.gz dumps/latest.sql.gz.last')

        sudo('pg_dump %s | gzip > %s' % (_connection_string(env, dba=True), rdump_path))
        sudo('chown %s:%s %s' % (env.user, env.user, rdump_path))
        sudo('chmod go-rwx %s' % rdump_path)

        with settings(warn_only=True):
            sudo('rm %s' % 'dumps/latest.sql.gz')
        get(rdump_path, 'dumps/latest.sql.gz')
        local('chmod o-rwx %s' % 'dumps/latest.sql.gz')

@task
def force_push():
    execute(push, really=True)

@task
def push(really=False):
    """ Recreate database from dumps/latest.sql.gz. """

    if env.env_name in ['production'] and not really:
        print "Overwriting the db in an environment called '%s' sounds dangerous." % env.env_name
        print "Use database.force_push instead."
        abort(0x6539d5)

    require('db_user', 'dba')
    sudo('mkdir -p %s' % os.path.dirname(rdump_path))
    
    if (not exists(rdump_path)
            or (remote_md5(rdump_path) != local_md5('dumps/latest.sql.gz'))
            or hasattr(env, 'FORCE_DATABASE_PUSH')):
        put('dumps/latest.sql.gz', rdump_path, use_sudo=True)
        sudo('chown %s:%s %s' % (env.user, env.user, rdump_path))
        sudo('chmod go-rwx %s' % rdump_path)
    else:
        print "-----> remote dumpfile is the same as local - not pushing"

    connection_string = _connection_string(env, dba=True)
    with settings(warn_only=True):
        run('dropdb %s' % connection_string)
    run('createdb -O %s %s' % (env.db_user, connection_string))
    #  When this bug is fixed: http://trac.osgeo.org/postgis/ticket/2223
    #  we can add "-v ON_ERROR_STOP=1" to this line
    run('gunzip -c %s | psql %s' % (rdump_path, connection_string))

@task
def migrate():
    """ Run south migrations to upgrade database """
    require('remote_path')
    with cd(env.remote_path):
        run("./manage.py syncdb --noinput", warn_only=True)
        run("./manage.py migrate --noinput --list") # Run this to get the state of things first
        run("./manage.py migrate --noinput")

