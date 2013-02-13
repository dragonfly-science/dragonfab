dragonfab
=========

## Debian packaging

Debian packages for used for deploying. Essentially, a fabfile should 
have tools to build the package, ship it to the destination, and install it.

## Database and file syncing

The script also handles the shipping around of application state, in the form
of the database and (potentially) uploaded files etc.

## Environments

dragonfab allows different environments to be defined in an environments.py file.

The contents of that file is expected to be a single python dictionary called
environments, e.g.:

environments = {
    'production': {
         'hosts': ['app.example.com'],
         'debconf': 'debconf.dat.production',
         }
    'lxc': {
         'lxc': 'example-lxc',
         'debconf': 'debconf.dat.lxc',
         }
    ...
}

This example would create fab commands 'lxc' and 'production' which can be used to
set the active environment. e.g.

     $ fab production deploy

would run the 'deploy' command after first activating the production environment.
This example simply involves changing the settings 'hosts' and 'debconf' in the
fabric env variable, but the 'lxc' example allows for setting up a LXC instance named
'example-lxc'. See dragonfab.env for more details on how this works.

An LXC is essentially a stripped down virtual machine, and similar to the concept of
a FreeBSD "jail". If LXC container are missing, they are cloned from an image
called "vanilla" by default, you can change this by specifying 'lxc_template' in
the environments dictionary.

Generally, most projects are expected to provide the follow environments: 
    * A local LXC development environment called 'lxc'.
    * "testing" environment, which uses LXC containers on the testing machine
      (currently 'titi') and is potentially almost identical to the local lxc
      environment.
    * "staging", a live environment (lxc or server) which can be accessed by
       clients and used for User Acceptance Testing but is not actively in use.
    * "production", live and actively used.

LXC environments are currently expected to be hosted locally, but eventually this
script should be configured to allow remote lxc deployment.

## Example

A test deployment process might look like:

$ fab <env> init        # perform any necessary first time setup
$ fab <env> deb.build   # build deb 
$ fab <env> deb.deploy  # deploy deb to lxc/server
$ fab <env> db_clone    # copy db from production server
$ fab <env> db_migrate  # perform any pending db migrations
$ fab <env> data_refresh # copy/rsync any media or data files needed from 
$ fab <env> web_restart # restart web server process
$ fab <env> test        # test application (django tests, phantomjs tests, and integration tests)

A production deployment needs to consider temporary downtime:

$ fab <env> init        # perform any necessary first time setup
$ fab <env> deb.build   # build deb 
$ fab <env> web_mode:maintenance # Go into maintenance mode, which replaces app with temporary splash page.
$ fab <env> deb.deploy  # deploy deb to lxc/server
$ fab <env> db_migrate  # perform any pending db migrations
$ fab <env> test        # test application (django tests, phantomjs tests, and integration tests)
$ fab <env> web_mode:live # Go into maintenance mode, which replaces app with temporary splash page.

<env> should be replaced by environment being used, e.g. lxc, production, etc.

In addition, a "deploy" in the root fabfile should be provided to wrap this entire
process so that someone can just run 'fab <env> deploy' instead of each
individual command.

Note, this is a guide only, inevitably there will be some project specific setup required.

## TODO

* make the sequence of deployment commands for an environment part of the environments.py
  definition, that way deployhub can introspect the sequence and we can also provide
  the root "deploy" command automatically.
* provide a db module that can handle creating a dump from a database, using cuckoo, etc.
* perhaps use 'fab init' to locally setup the current machine, useful for new
  developers?
* Read and ponder on this: http://hynek.me/articles/python-app-deployment-with-native-packages/

