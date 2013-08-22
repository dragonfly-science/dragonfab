import os

from fabric.api import local, env, task, sudo, lcd, put, run, cd, settings, get, require

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
        if val in env:
            conn_str += ' %s %s' % (param, env.get(val))
    conn_str += ' '
    return conn_str

@task
def dump():
    """Copy of current database from the production server to dumps/latest.sql"""
    require('local_path')
    with lcd(env.local_dir):
        local('mkdir -p dumps')
        if os.path.exists('dumps/latest.sql'):
            local('mv dumps/latest.sql dumps/latest.sql.last')
        sudo('mkdir -p /var/backups/dumps/')

        sudo('pg_dump %s > /var/backups/dumps/latest.sql' % _connection_string(env))

        get('/var/backups/dumps/latest.sql', 'dumps/latest.sql')
        sudo('rm /var/backups/dumps/latest.sql')

@task
def push():
    "Recreate database from dumps/latest.sql."
    require('db_user', 'dba')

    sudo('mkdir -p /var/backups/dumps/')
    put('dumps/latest.sql', '/var/backups/dumps/latest.sql', use_sudo=True)
    connection_string = _connection_string(env, dba=True)
    with settings(warn_only=True):
        run('dropdb %s' % connection_string)
    run('createdb -O %s %s' % (env.db_user, connection_string))
    #  When this bug is fixed: http://trac.osgeo.org/postgis/ticket/2223
    #  we can add "-v ON_ERROR_STOP=1" to this line
    run('psql %s -f /var/backups/dumps/latest.sql' % connection_string)

@task
def migrate():
    require('remote_path')
    "Run south migrations to upgrade database"
    with cd(env.remote_path):
        run("./manage.py syncdb --noinput")
        run("./manage.py migrate --list") # Run this to get the state of things first
        run("./manage.py migrate")

