#!/usr/bin/env python
# encoding: utf-8

"""
Provides a simple nntp checker.
"""

# stdlib
import nntplib
import os, sys
from copy import deepcopy
from itertools import chain


# 3rd party
import yaml
import keyring


FILE = os.path.abspath(os.path.expanduser("~/.nntp.yml"))
PORT = 119
DEFAULTS = {
        "server" : {
            "user" : None,
            "host" : None,
            "port" : PORT,
            #"password" : None
            },
        "groups" : [],
        "indicator" : {
            "interval" : 10,
            },
        "seen" : {},
        }

class RequiresLogin(Exception):
    """ Just to know what it is."""
    pass

class BadConfig(Exception):
    """ Just to know what it is."""
    pass

def needs_login(func):
    """ Ensures that the server is logged in first. """
    def wrapper(self, *args, **kwargs):
        """ Wraps the func. """
        if not self.server:
            raise RequiresLogin()
        return func(self, *args, **kwargs)
    return wrapper

class NNTPCheck(object):
    """ A simple nntp checker. """
    def __init__(self, seen):
        self.seen = seen
        self.server = None

    def login(self, host, user=None, passwd=None, port=119):
        """ Log into the server. """
        self.server = nntplib.NNTP(host, port, user, passwd)

    def get_seen(self, group):
        """ Gets the id of the last message marked read in this group. """
        return self.seen.get(group, 0)

    @needs_login
    def new_subs(self, group):
        """ Gets the list of new messages in group. """
        seen = self.get_seen(group)
        _resp, count, first, last, _name = self.server.group(group)
        count, first, last, seen = int(count), int(first), int(last), int(seen)
        if last > seen:
            req = "%s-%s" % (max(seen, first), last)
            _resp, subs = self.server.xhdr('subject', req)
            return subs
        return []

def get_server(config, passwd):
    """ Gets a server given a config file and password. """
    try:
        user = config["server"].get("user", None)
        host = config["server"]["host"]
        port = config["server"].get("port", PORT)
    except KeyError:
        user = host = port = None

    if not host or not port:
        raise BadConfig("Missing informaion, config file must contain host")

    checker = NNTPCheck(config["seen"])

    checker.login(host, user, passwd, port=port)

    return checker

def get_config(filename):
    """ Reads in a config filename. """
    try:
        with open(filename) as fil:
            return yaml.load(fil)
    except IOError:
        return {}

def save_config(conf, filename):
    """ saves a config filename to the given path. """
    with open(filename, "w") as fil:
        yaml.dump(conf, fil, default_flow_style=False)

def get_merged_config(conf):
    """ Merges the default values with the config data given. """
    merged = dict(chain(DEFAULTS.items(), conf.items()))
    return deepcopy(merged)


def set_passwd(user, host, passwd):
    """ Sets the password in the keychain. """
    key = "nntp://%s" % host

    keyring.set_password(key, user, passwd)

def get_password(conf):
    """ Gets the password from the keychain, or conf file. """
    user = conf["server"].get("user", None)
    host = conf["server"]["host"]
    key = "nntp://%s" % host

    if not user:
        return None

    passwd = conf["server"].get("password", None)

    if not passwd:
        passwd = keyring.get_password(key, user)

    return passwd or None
