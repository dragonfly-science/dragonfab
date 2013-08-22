environments = {
    'production': {
        'hosts': ['example.com'],
        'debconf': 'debconf.dat',
        },
    'staging': {
        'debconf': 'debconf.dat',
        },
    'lxc': {
        'lxc': 'example-lxc',
        'lxc_template': 'vanilla', # optional
        },
    '__all__': {
        'dba': 'dba'
        }
}
