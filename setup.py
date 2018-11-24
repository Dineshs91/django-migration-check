import codecs
import os
import re

from setuptools import setup


setup(
    name='django-migration-check',
    version="0.1.0",
    description=(
        'This package checks for destructive migrations.'
    ),
    url='https://github.com/dineshs91/django-migration-check',
    packages=['migration_check'],
    license='MIT License',
    keywords='django migrations',
    platforms=['any'],
    install_requires=[],
    python_requires='>=3, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*',
    classifiers=[
        'Framework :: Django :: 2.0',
        'Framework :: Django :: 2.1',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
