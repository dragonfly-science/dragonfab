from setuptools import setup

setup(name = "dragonfab",
    version = "1.4.0",
    description = "Fabric support",
    author = "Joel Pitt",
    author_email = "joel@joelpitt.com",
    url = "https://github.com/dragonfly-science/dragonfab",
    install_requires = ['fabric', 'pip>=1.4', 'wheel', 'docker-py'],
    packages = ['dragonfab'],
)
