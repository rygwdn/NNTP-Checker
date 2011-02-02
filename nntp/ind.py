#!/usr/bin/env python
# encoding: utf-8

import nntp
from nntp import BadConfig

import pynotify
import indicate
import gobject
import gtk

import thread, threading
import time
import os, sys
from nntplib import NNTPTemporaryError

APP_NAME = "NNTP Checker"
FILE = "tst.yml" # nntp.FILE
checker = None
srv = None

def notify(mess, title=APP_NAME):
    notif = pynotify.Notification(title, mess)
    notif.show()

class Server(object):
    def __init__(self, desktop, actions_top=True):
        self.groups = {}
        self.actions = {}
        self.user_cb = None
        self.server_cb = None
        self.desktop = desktop
        self.actions_top = actions_top

        self.srv = indicate.indicate_server_ref_default()
        self.srv.set_type("message.news")
        self.srv.set_desktop_file(desktop)
        self.srv.connect('server-display', self.server_display)
        self.srv.show()

    def set_group(self, name, count):
        init_count = 0

        if name in self.groups:
            ind = self.groups[name]
            init_count = int(ind.get_property('count'))
        else:
            ind = indicate.Indicator()
            self.groups[name] = ind

        ind.set_property('name', name)
        ind.set_property('count', str(count))
        if count > init_count:
            ind.set_property('draw-attention', 'true')
            if count > 1:
                mess = "New message in %s" % name
            else:
                mess = "%s new messages in %s" % (count, name)
            notify(mess)
        if count == 0:
            ind.set_property('draw-attention', 'false')

        ind.connect('user-display', self.user_display)
        ind.show()

        return ind

    def hide_group(self, name):
        try:
            self.groups[name].hide()
            del self.groups[name]
        except KeyError:
            print "Tried to hide non-existant group: ", name

    def hide_all(self):
        for group in self.groups.keys():
            self.hide_group(group)
        for action in self.actions.keys():
            self.del_action(action)

    def add_clear(self, func):
        def clear(ind, id):
            func()
        if "Clear" not in self.actions:
            self.add_action("Clear", clear)

    def add_action(self, name, cb):
        ind = indicate.Indicator()
        self.actions[name] = ind
        ind.set_property('name', name)
        ind.set_property('subtype', 'menu')
        ind.connect('user-display', cb)
        ind.show()
        return ind

    def del_action(self, name):
        try:
            self.actions[name].hide()
            del self.actions[name]
        except KeyError:
            print "Tried to remove non-existant action: ", name

    # Click name
    def server_display(self, srv, id):
        print "server selected"

    # Click item
    def user_display(self, ind, id):
        print "group selected"

class Checker(object):
    def __init__(self, ind_server):
        self.conf = nntp.get_config(FILE)
        self.merged = nntp.get_merged_config(self.conf)
        passwd = nntp.get_password(self.merged)
        self.server = nntp.get_server(self.merged, passwd)
        self.ind_server = ind_server
        self.interval = self.merged["indicator"]["interval"]

    def run(self):
        try:
            self.do_count()
        except NNTPTemporaryError, e:
            if "Authent" in str(e):
                mess = "Authentication error"
            else:
                mess = "Error checking messages: %s" % e
            notify(mess)

        gobject.timeout_add_seconds(self.interval, self.run)

    def do_count(self):
        for group in self.merged["groups"]:
            subs = self.server.new_subs(group)
            if subs:
                self.ind_server.add_clear(self.clear)
                self.ind_server.set_group(group, len(subs))

    def clear(self):
        for group in self.merged["groups"]:
            subs = self.server.new_subs(group)
            if subs:
                last, sub = subs[-1]
                self.merged["seen"][group] = int(last)
                self.conf["seen"][group] = int(last)
                nntp.save_config(self.conf, FILE)
            self.ind_server.hide_all()
        self.run()

def main():
    gtk.gdk.threads_init()

    curdir = os.getcwd()
    desktop_file = os.path.join(curdir, "nntp-checker.desktop")
    pynotify.init(APP_NAME)

    try:
        srv = Server(desktop_file)
        checker = Checker(srv)
    except Exception, e:
        mess = "Error checking messages: %s" % e
        sys.exit(1)

    gobject.timeout_add_seconds(1, checker.run)
    gtk.main()

if __name__ == "__main__":
    main()
