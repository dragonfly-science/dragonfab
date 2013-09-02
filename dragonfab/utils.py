from fabric.api import env, sudo, task, execute, require

maintenance_lock = 'maintenance.lock'

@task
def maintenance_on():
    """ Add maintenance lock file and restart apache """
    require('remote_path')
    sudo('touch %s/%s' % (env.remote_path, maintenance_lock))
    execute('apache_restart')

@task
def maintenance_off():
    """ Remove maintenance lock file and restart apache """
    require('remote_path')
    sudo('rm -f %s/%s' % (env.remote_path, maintenance_lock))
    execute('apache_restart')

@task
def apache_restart():
    """ Restart Apache """
    sudo('sleep 2')
    # http://stackoverflow.com/questions/6379484/fabric-appears-to-start-apache2-but-doesnt
    sudo('service apache2 restart', pty=False)
