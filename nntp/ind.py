#!/usr/bin/env python
# encoding: utf-8

"""
Provides an indicator applet for the nntp checker.
"""

import nntp

import pynotify
import indicate
import gobject
import gtk

import os, sys
from nntplib import NNTPTemporaryError

APP_NAME = "NNTP Checker"
FILE = "tst.yml" # nntp.FILE

def notify(mess, title=APP_NAME):
    """ Display a notification to user. """
    notif = pynotify.Notification(title, mess)
    notif.show()

class IndicatorServer(object):
    """ Provides an interface to the indicator applet system. """
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
        """ Sets the count for a group. """
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
        """ Hide and remove a group from the indicator. """
        try:
            self.groups[name].hide()
            del self.groups[name]
        except KeyError:
            print "Tried to hide non-existant group: ", name

    def hide_all(self):
        """ Hide everything. """
        for group in self.groups.keys():
            self.hide_group(group)
        for action in self.actions.keys():
            self.del_action(action)

    def add_clear(self, func):
        """ Adds the clear option, which calls func. """
        def clear(_ind, _uid):
            """ Called by the indicator. """
            func()
        if "Clear" not in self.actions:
            self.add_action("Clear", clear)

    def add_action(self, name, callback):
        """ Adds an action to the indicator. """
        ind = indicate.Indicator()
        self.actions[name] = ind
        ind.set_property('name', name)
        ind.set_property('subtype', 'menu')
        ind.connect('user-display', callback)
        ind.show()
        return ind

    def del_action(self, name):
        """ Deletes an action from the indicator. """
        try:
            self.actions[name].hide()
            del self.actions[name]
        except KeyError:
            print "Tried to remove non-existant action: ", name

    # Click name
    def server_display(self, _srv, _id):
        """ Dummy, called when app name clicked. """
        pass
        #print "server selected"

    # Click item
    def user_display(self, _ind, _id):
        """ Dummy, called when a group is clicked. """
        pass
        #print "group selected"

class Checker(object):
    """ Checks the nntp server for new items. """
    def __init__(self, ind_server):
        self.conf = nntp.get_config(FILE)
        self.merged = nntp.get_merged_config(self.conf)
        passwd = nntp.get_password(self.merged)
        self.server = nntp.get_server(self.merged, passwd)
        self.ind_server = ind_server
        self.interval = self.merged["indicator"]["interval"]

    def run(self):
        """ Runs the loop by checking for new items, then adding
        a callback for itself.
        """
        try:
            self.do_count()
        except NNTPTemporaryError, err:
            if "Authent" in str(err):
                mess = "Authentication error"
            else:
                mess = "Error checking messages: %s" % err
            notify(mess)

        gobject.timeout_add_seconds(self.interval, self.run)

    def do_count(self):
        """ Checks for new messages on the server and sets the group counts.
        """
        for group in self.merged["groups"]:
            subs = self.server.new_subs(group)
            if subs:
                self.ind_server.add_clear(self.clear)
                self.ind_server.set_group(group, len(subs))

    def clear(self):
        """ Clears everything from the indicator, and marks items as read. """
        for group in self.merged["groups"]:
            subs = self.server.new_subs(group)
            if subs:
                last, _sub = subs[-1]
                self.merged["seen"][group] = int(last)
                self.conf["seen"][group] = int(last)
                nntp.save_config(self.conf, FILE)
            self.ind_server.hide_all()
        self.run()

def main():
    """ Runs the main program. """
    gtk.gdk.threads_init()

    curdir = os.getcwd()
    desktop_file = os.path.join(curdir, "nntp-checker.desktop")
    pynotify.init(APP_NAME)

    try:
        srv = IndicatorServer(desktop_file)
        checker = Checker(srv)
    except Exception, err: #pylint: disable=W0703
        mess = "Error checking messages: %s" % err
        notify(mess)
        sys.exit(1)

    gobject.timeout_add_seconds(1, checker.run)
    gtk.main()

if __name__ == "__main__":
    main()
