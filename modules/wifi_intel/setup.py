from setuptools import setup, find_packages


def readme():
    with open('README.md') as f:
        return f.read()


setup(
    name='uniflex_module_wifi_intel',
    version='0.1.0',
    packages=find_packages(),
    url='https://github.com/uniflex',
    license='',
    author='Tolja Zubow',
    author_email='zubow@tu-berlin.de',
    description='UniFlex WiFI Intel Modules',
    long_description='UniFlex Intel WiFi Modules',
    keywords='wireless control',
    install_requires=['numpy']
)
