from setuptools import setup

setup(name = "dragonfab",
    version = "1.3.0",
    description = "Fabric support",
    author = "Joel Pitt",
    author_email = "joel@joelpitt.com",
    url = "https://github.com/ferrouswheel/dragonfab",
    install_requires = ['fabric', 'pip>=1.4', 'wheel'],
    packages = ['dragonfab'],
)
