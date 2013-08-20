dragonfab
=========

Dragonfab is a small Fabric library which allows for environments using a number
of predefined environments. These support normal hosts, but also LXCs on the machine
running fabric.

## Environments

dragonfab allows different environments to be defined in an environments.py file.

The contents of that file is expected to be a single python dictionary called
environments, e.g.:

```python
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
```

This example would create fab commands 'lxc' and 'production' which can be used to
set the active environment. e.g.

    $ fab production deploy

would run the 'deploy' command after first activating the production environment.
This example just involves changing the settings 'hosts' and 'debconf' in the
fabric env variable, but the 'lxc' example allows for setting up a LXC instance named
'example-lxc'. See dragonfab.env for more details on how this works.

An LXC is essentially a stripped down virtual machine, and similar to the concept of
a FreeBSD "jail". If a LXC container is missing, it is cloned from an image
called "vanilla" by default, you can change this by specifying 'lxc_template' in
the environments dictionary.

Generally, most projects are expected to provide the follow environments: 

* `lxc` - local LXC development environment.
* `testing` - uses LXC containers on the testing machine
  and is potentially almost identical to `lxc`.
* `staging` - a live environment (lxc or server) which can be accessed by
  clients and used for User Acceptance Testing but is not actively in use.
* `production` - live and actively used.

LXC environments are currently expected to be hosted locally, but eventually this
script should be configured to allow remote lxc deployment.

There is also a special environment `__all__`, which you can use if you want to
define environmental variables common to all environments. The default will be
overwritten if a specific environment also contains the variable. e.g.

```python
environments = {
    'production': {
         'hosts': ['app.example.com'],
         'debconf': 'debconf.dat.production',
         }
    'staging': {
         'hosts': ['staging.example.com'],
         'db_host': 'stagingdb',
         }
    '__all__': {
         'db_host': 'db',
         }
    ...
}
```

Here, the `db_host` default is used by production, but the staging environment
overwrites this with it's own value.

### Environment variables

dragonfab's environment, at the most basic level, replaces variables in
Fabric's `env` module which is used for configuration of hosts and many other things.

In addition to the variables that Fabric knows what to do with, we define a number
of new variables that dragonfab uses.

* `remote_path` - This is used for a relative path management. Don't specify it
  if you want to use absolute paths for other path variables. Must end in a trailing
  slash.
* `lxc` - The lxc to create, start, connect to, for running fabric commands.
* `lxc_template` - The lxc that is used as a tempalte to create `lxc` if it is
  missing. Looks for an lxc `vanilla` by default.
* `debconf` - The file that is used for configuring a debian package when the
  `deb.deploy` command is executed.

## Debian packaging

Debian packages are used for deployment. Essentially, a fabfile should 
have tools to build the package, ship it to the destination, and install it.

dragonfab provides:

* `deb.build` - Builds a .deb file from the current project, ready to be
  installed. This expects a `debian/` subdirectory to be present with packaging
  details.
* `deb.deploy` - Deploy the most recently created deb, using the debconf.dat
  of the current environment.

## Database and file syncing

dragonfab also provides tools to ship around application state. In particular, the
database and media that is not in the code repository (uploaded files etc.)

dragonfab provides:

* `database.dump` - Get a dump from a postgresql database.
* `database.push` - Take a dump and load it into a postgresql database.
* `database.migrate` - Perform pending db migrations (using south's 'migrate' command).

These commands expect the following env variables, either as constants in the
fabfile, or defined in environments.py.

* `db_user` - The user the database belongs to.
* `dba` - A database admin with permissions to create/drop dbs, and assign ownership. (for push only)

Optionally:

* `db_password` - The user's password, no password assumes it's not needed.
* `db_port` - The port, if missing assume default or local socket.
* `db_host` - The host, if missing assume local socket.

## Example

A test deployment process might look like:

```
$ fab <env> init        # perform any necessary first time setup
$ fab <env> deb.build   # build deb 
$ fab <env> deb.deploy  # deploy deb to lxc/server
$ fab <env> db_clone    # copy db from production server
$ fab <env> db_migrate  # perform any pending db migrations
$ fab <env> data_refresh # copy/rsync any media or data files needed from 
$ fab <env> web_restart # restart web server process
$ fab <env> test        # test application (django tests, phantomjs tests, and integration tests)
```

A production deployment needs to consider temporary downtime:

```
$ fab <env> init        # perform any necessary first time setup
$ fab <env> deb.build   # build deb 
$ fab <env> web_mode:maintenance # Go into maintenance mode, which replaces app with temporary splash page.
$ fab <env> deb.deploy  # deploy deb to lxc/server
$ fab <env> db_migrate  # perform any pending db migrations
$ fab <env> test        # test application (django tests, phantomjs tests, and integration tests)
$ fab <env> web_mode:live # Go into maintenance mode, which replaces app with temporary splash page.
```

`<env>` should be replaced by environment being used, e.g. lxc, production, etc.

In addition, a `deploy` in the root fabfile should be provided to wrap this entire
process so that someone can just run `fab <env> deploy` instead of each
individual command.

Note, this is a guide only, inevitably there will be some project specific setup required.

## TODO

* make the sequence of deployment commands for an environment part of the environments.py
  definition, that way deployhub could introspect the sequence and we can also provide
  the root "deploy" command automatically.
* provide a db module that can handle creating a dump from a database, using cuckoo, etc.
* perhaps use 'fab init' to locally setup the current machine, useful for new
  developers?
* Read and ponder on this: http://hynek.me/articles/python-app-deployment-with-native-packages/
