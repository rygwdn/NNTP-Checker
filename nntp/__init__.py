#!/usr/bin/env python
# encoding: utf-8

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
    pass #TODO

class BadConfig(Exception):
    pass #TODO

def needs_login(func):
    def wrapper(self, *args, **kwargs):
        if not self.s:
            raise RequiresLogin()
        return func(self, *args, **kwargs)
    return wrapper

class NNTPCheck(object):
    def __init__(self, seen):
        self.seen = seen
        self.s = None

    def login(self, host, user, passwd, port=119):
        self.s = nntplib.NNTP(host, port, user, passwd)

    def get_seen(self, group):
        return self.seen.get(group, 0)

    @needs_login
    def new_subs(self, group):
        seen = self.get_seen(group)
        resp, count, first, last, name = self.s.group(group)
        count, first, last, seen = int(count), int(first), int(last), int(seen)
        if last > seen:
            req = "%s-%s" % (max(seen, first), last)
            resp, subs = self.s.xhdr('subject', req)
            return subs
        return []

def get_server(config, passwd):
    try:
        user = config["server"].get("user", None)
        host = config["server"]["host"]
        port = config["server"].get("port", PORT)
    except KeyError:
        user = host = port = None

    if not host or not port:
        raise BadConfig("Missing informaion, config file must contain user and host")

    checker = NNTPCheck(config["seen"])

    checker.login(host, user, passwd, port=port)

    return checker

def get_config(file):
    try:
        with open(file) as f:
            return yaml.load(f)
    except IOError:
        return {}

def save_config(conf, file):
    with open(file, "w") as f:
        yaml.dump(conf, f, default_flow_style=False)

def get_merged_config(conf):
    merged = dict(chain(DEFAULTS.items(), conf.items()))
    return deepcopy(merged)


def set_passwd(user, host, passwd):
    key = "nntp://%s" % host

    keyring.set_password(key, user, passwd)

def get_password(conf, prompt=False):
    user = conf["server"].get("user", None)
    host = conf["server"]["host"]
    key = "nntp://%s" % host

    if not user:
        return None

    passwd = conf["server"].get("password", None) # TODO: doc this

    if not prompt and not passwd:
        passwd = keyring.get_password(key, user)

    return passwd or None
