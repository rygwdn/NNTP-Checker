#!/usr/bin/env python
# encoding: utf-8

from setuptools import setup, find_packages
setup(
    name = "NNTPChecker",
    version = "0.1",
    packages = find_packages(),

    # Project uses reStructuredText, so ensure that the docutils get
    # installed or upgraded on the target machine
    install_requires = ['PyYAML', 'keyring'],
    extras_require = {
        "ind" : ['gtk', 'pynotify', 'indicate', 'gobject']
        },

    package_data = {
        # If any package contains *.txt or *.rst files, include them:
        '': ['*.txt', '*.rst'],
    },

    entry_points = {
            "console_scripts": ["nntp-cli=nntp.cli:main"],
            "gui_scripts": ["nntp-indicator=nntp.ind:main"],
            },

    data_files   = [
            ('/usr/share/icons/hicolor/16x16/apps', ['misc/nntp-indicator.png']),
            ('/usr/share/applications', ['misc/nntp-indicator.desktop'])
            #('share/man/man1', ['man/nntp.1']),
            #('share/pixmaps', ['pixmaps/nntp.png']),
            ],

    # metadata for upload to PyPI
    platforms    = ['any'],
    author = "Ryan Wooden",
    author_email = "rygwdn@gmail.com",
    description = "Checks groups on an nntp server for messages. Provides an indicator applet, and a cli checker",
    license = "GPL",
    keywords = "nntp news indicator applet",
    #url = "http://example.com/HelloWorld/",   # project home page, if any

    # could also include long_description, download_url, classifiers, etc.
)
