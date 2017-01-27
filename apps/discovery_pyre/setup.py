from setuptools import setup, find_packages


def readme():
    with open('README.md') as f:
        return f.read()


setup(
    name='uniflex_app_discovery_pyre',
    version='0.1.0',
    packages=find_packages(),
    url='https://github.com/uniflex',
    license='',
    author='Piotr Gawlowicz',
    author_email='gawlowicz@tu-berlin.de',
    description='UniFlex PYRE Discovery Module',
    long_description='Implementation of a Dynamic Discovery Module.',
    keywords='wireless control',
    install_requires=['pyre>=0.3'],
)
