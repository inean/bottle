#!/usr/bin/env python

import sys
from setuptools import setup

if sys.version_info < (2, 5):
    raise NotImplementedError(
        "Sorry, you need at least Python 2.5 or Python 3.x to use routes.")

import btlroute

setup(
    name='btlroute',
    version=btlroute.__version__,
    description='URL Route parser HEAVILY based on Bottle Web server',
    long_description=btlroute.__doc__,
    author=btlroute.__author__,
    author_email=['marc@gsites.de', 'inean.es@gmail.com'],
    py_modules=['btlroute'],
    license='MIT',
    platforms='any',
    test_suite='test',
    classifiers=['Development Status :: 4 - Beta',
                 'Intended Audience :: Developers',
                 'License :: OSI Approved :: MIT License',
                 'Topic :: Software Development :: Libraries',
                 'Programming Language :: Python :: 2.5',
                 'Programming Language :: Python :: 2.6',
                 'Programming Language :: Python :: 2.7',
                 'Programming Language :: Python :: 3'],
)
