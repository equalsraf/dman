# coding: utf-8
#!python
"distutils package - dman"
from distutils.core import setup

setup(name='dman',
    classifiers=[
        'Operating System :: POSIX',
        'Development Status :: 4 - Beta',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 2',
    ],
    version='0.0dev',
    description='The meta download manager',
    author='Rui Abreu Ferreira',
    author_email='raf-ep@gmx.com',
    url='https://bitbucket.org/equalsraf/dman',
    packages=['dman'],
    scripts=['scripts/dman'],
    long_description='dman is a download manager interface written in python',
    install_requires=[
        'twisted',
    ],
)


