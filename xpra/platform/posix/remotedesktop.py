#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# This file is part of Xpra.
# Copyright (C) 2023 Antoine Martin <antoine@xpra.org>
# Xpra is released under the terms of the GNU GPL v2, or, at your option, any
# later version. See the file COPYING for details.

import gi
gi.require_version("Gdk", "3.0")
from gi.repository import Gdk
from dbus.types import UInt32, Int32

from xpra.util import net_utf8
from xpra.dbus.helper import native_to_dbus
from xpra.platform.xposix.fd_portal import REMOTEDESKTOP_IFACE
from xpra.platform.xposix.fd_portal_shadow import PortalShadow
from xpra.log import Logger

log = Logger("shadow")
keylog = Logger("shadow", "keyboard")
mouselog = Logger("shadow", "mouse")


class RemoteDesktop(PortalShadow):
    def __init__(self, multi_window=True):
        super().__init__(multi_window)
        self.input_devices = 0
        self.keymap = Gdk.Keymap.get_default()
        if not self.keymap:
            log.warn("Warning: no access to the keymap, cannot simulate key events")

    def get_server_mode(self):
        return "pipewire shadow"


    def set_keymap(self, server_source, force=False):
        keylog.info("key mapping not implemented - YMMV")


    def do_process_mouse_common(self, proto, device_id, wid, pointer, props):
        if self.readonly or not self.input_devices:
            return False
        win = self._id_to_window.get(wid)
        if not win:
            mouselog.error(f"Error: window {wid} not found")
            return
        x, y = pointer[:2]
        node_id = win.pipewire_id
        options = native_to_dbus([], "{sv}")
        self.portal_interface.NotifyPointerMotionAbsolute(
            self.session_handle,
            options,
            node_id,
            x, y,
            dbus_interface=REMOTEDESKTOP_IFACE)

    def do_process_button_action(self, proto, device_id, wid, button, pressed, pointer, props):
        options = native_to_dbus([], "{sv}")
        mouselog(f"button-action: button={button}, pressed={pressed}")
        evdev_button = {
            1   : 0x110,    #BTN_LEFT
            2   : 0x111,    #BTN_RIGHT
            3   : 0x112,    #BTN_MIDDLE
            }.get(button, -1)
        if evdev_button<0:
            mouselog.warn(f"Warning: button {button} not recognized")
            return
        self.portal_interface.NotifyPointerButton(
            self.session_handle,
            options,
            Int32(evdev_button),
            UInt32(pressed),
            dbus_interface=REMOTEDESKTOP_IFACE)


    def _process_key_action(self, proto, packet):
        if self.readonly or not self.input_devices or not self.keymap:
            return
        wid, keyname, pressed, modifiers, keyval, keystr, client_keycode, group = packet[1:9]  # @UnusedVariable
        ss = self.get_server_source(proto)
        if ss is None:
            return
        keyname = net_utf8(keyname)
        keystr = net_utf8(keystr)
        modifiers = list(net_utf8(x) for x in modifiers)
        self.set_ui_driver(ss)
        keylog(f"key: name={keyname}, keyval={keyval}, keystr={keystr}")
        options = native_to_dbus([], "{sv}")
        #if keystr:
        #    keysym = Gdk.KEY_0
        #    self.portal_interface.NotifyKeyboardKeysym(
        #        self.session_handle,
        #        options,
        #        Int32(keysym),
        #        UInt32(pressed))
        #GDK code must be moved elsewhere
        ukeyname = keyname[:1].upper()+keyname[2:]
        skeyval = getattr(Gdk, f"KEY_{keyname}", 0) or getattr(Gdk, f"KEY_{ukeyname}", 0) or keyval
        entries = self.keymap.get_entries_for_keyval(skeyval)
        keylog(f"get_entries_for_keyval({skeyval})={entries}")
        if not entries or not entries[0]:
            keylog(f"no matching entries in keymap for {skeyval}")
            return
        for keymapkey in entries[1]:
            keycode = keymapkey.keycode-8
            if keycode<=0:
                continue
            self.portal_interface.NotifyKeyboardKeycode(
                self.session_handle,
                options,
                Int32(keycode),
                UInt32(pressed),
                dbus_interface=REMOTEDESKTOP_IFACE)