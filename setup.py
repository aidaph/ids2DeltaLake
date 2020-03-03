# -*- coding: utf-8 -*-

# Learn more: https://github.com/kennethreitz/setup.py

from setuptools import setup, find_packages

import u2toparquet

with open('README.rst') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='u2toparquet',
    version='0.1.0',
    description='Convert U2 files to Parquet',
    long_description=readme,
    author='Kenneth Reitz',
    author_email='aidaph@ifca.unican.es',
    url='https://github.com/aidaph/u2toparquet',
    license=license,
    packages=find_packages(exclude=('tests', 'docs')),
    scripts = [
        "bin/u2toparquet",
    ],
)
