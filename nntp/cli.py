#!/usr/bin/env python
# encoding: utf-8

"""
Provides a cli interface to the nntp checker.
"""

import argparse
import getpass
import sys

import nntp
from nntp import BadConfig

def parse_opts(opts=None):
    """ Parse the arguments. """
    parser = argparse.ArgumentParser(description="nntp news checker")

    parser.add_argument("action", default="count", nargs="?",
            choices=["count", "list", "mark"],
            help="The action to perform, where 'count' gives a short"
                + " list of the number of new messages, 'list' gives a long"
                + " list, and 'mark' markes all messages as read")

    parser.add_argument('--host',
            help="the host")
    parser.add_argument('--port', '-p', type=int,
            help="the port")
    parser.add_argument('--user', '-u',
            help="the username for the server")
    parser.add_argument('--passwd', action='store_true',
            help="prompt for a password")

    parser.add_argument('groups', nargs='*',
            help="a list of groups to check")

    parser.add_argument('--conf', '-c', default=nntp.FILE,
            help="The config file to use")
    parser.add_argument('--write-conf', action='store_true',
            help="Create a new config file (using the options provided)")

    parser.add_argument('--list-max', type=int, default=10,
            help="maximum number of items to list")

    if opts:
        args = parser.parse_args(opts)
    else:
        args = parser.parse_args()
    return args

def get_merged(conf, opts):
    """ Merges conf and opts. """
    merged = nntp.get_merged_config(conf)

    merged["action"] = opts.action

    if opts.host:
        merged["server"]["host"] = opts.host
    if opts.port:
        merged["server"]["port"] = opts.port
    if opts.user:
        merged["server"]["user"] = opts.user

    if opts.groups:
        merged["groups"] = opts.groups
    if opts.list_max:
        merged["listmax"] = opts.list_max

    return merged

def get_password(conf, prompt=False):
    """ Gets a password (possibly from the user). """
    user = conf["server"]["user"]
    host = conf["server"]["host"]

    if not host:
        raise BadConfig("Missing informaion, config file must contain host")

    passwd = nntp.get_password(conf)
    if not passwd or prompt:
        passwd = getpass.getpass("Password for %s@%s: " % (user, host))
        nntp.set_passwd(user, host, passwd)

    return passwd


def do_list(server, config):
    """ Long list of new messages. """
    for group in config["groups"]:
        subs = server.new_subs(group)
        if subs:
            print group
            for uid, sub in subs[-config["listmax"]:]:
                print uid, sub

def do_count(server, config):
    """ Short list of new messages. """
    for group in config["groups"]:
        subs = server.new_subs(group)
        if subs:
            print "%s: %s" % (group, len(subs))

def do_mark(server, config):
    """ Mark messages as read. """
    for group in config["groups"]:
        subs = server.new_subs(group)
        if subs:
            last, _sub = subs[-1]
            config["seen"][group] = int(last)


def main():
    """ Run the main program. """
    opts = parse_opts()
    config = nntp.get_config(opts.conf)
    merged = get_merged(config, opts)

    if opts.write_conf:
        nntp.save_config(merged, opts.conf)
    else:
        passwd = get_password(merged, opts.passwd)
        try:
            checker = nntp.get_server(merged, passwd)
        except BadConfig, exe:
            print exe
            sys.exit(1)

        if opts.action == "list":
            do_list(checker, merged)
        elif opts.action == "count":
            do_count(checker, merged)
        elif opts.action == "mark":
            do_mark(checker, merged)
            config["seen"] = merged["seen"]
            nntp.save_config(config, opts.conf)
        else:
            raise NotImplementedError("Invalid action")

if __name__ == '__main__':
    main()
