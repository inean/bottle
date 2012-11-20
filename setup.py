#!/usr/bin/env python

import sys
from setuptools import setup

if sys.version_info < (2,5):
    raise NotImplementedError("Sorry, you need at least Python 2.5 or Python 3.x to use routes.")

import btlroute

setup(name='btlroute',
      version=btlroute.__version__,
      description='Fast and simple WSGI-framework for small web-applications.',
      long_description=btlroute.__doc__,
      author=btlroute.__author__,
      author_email='marc@gsites.de',
      py_modules=['btlroute'],
      license='MIT',
      platforms = 'any',
      test_suite = 'test',
      classifiers=['Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Topic :: Internet :: WWW/HTTP :: HTTP Servers',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
        'Programming Language :: Python :: 2.5',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3'],
     )



