from setuptools import setup, find_packages
from setuptools.command.install import install
import os

setup(
    name='adjust',
    version=open('VERSION').read().strip(),
    #version=__version__,
    author='Viktor Nikitin, Francesco De Carlo',
    author_email='decarlof@gmail.com',
    url='https://github.com/xray-imaging/adjust.git',
    packages=find_packages(),
    include_package_data = True,
    scripts=['bin/adjust'],
    description='cli to run tomo auto alignment functions',
    zip_safe=False,
)