from setuptools import setup, find_packages


def readme():
    with open('README.md') as f:
        return f.read()


setup(
    name='uniflex_app_wireless_topology',
    version='0.1.0',
    packages=find_packages(),
    url='https://github.com/uniflex',
    license='',
    author='Piotr Gawlowicz, Anatolij Zubow',
    author_email='{gawlowicz, zubow}@tu-berlin.de',
    description='UniFlex Wireless Topology Module',
    long_description='Used to discover the wireless topology like nodes in reception range',
    keywords='wireless control',
    install_requires=[]
)
