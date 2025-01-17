# This file is part of Xpra.
# Copyright (C) 2010-2023 Antoine Martin <antoine@xpra.org>
# Copyright (C) 2008, 2010 Nathaniel Smith <njs@pobox.com>
# Xpra is released under the terms of the GNU GPL v2, or, at your option, any
# later version. See the file COPYING for details.

from typing import Any

from gi.repository import GLib, GObject  # @UnresolvedImport

from xpra.net.common import PacketType
from xpra.client.base.client import XpraClientBase, EXTRA_TIMEOUT
from xpra.exit_codes import ExitCode, ExitValue
from xpra.log import Logger

log = Logger("gobject", "client")


class GObjectXpraClient(GObject.GObject, XpraClientBase):
    """
        Utility superclass for GObject clients
    """
    COMMAND_TIMEOUT = EXTRA_TIMEOUT

    def __init__(self):
        self.glib_mainloop = None
        self.idle_add = GLib.idle_add
        self.timeout_add = GLib.timeout_add
        self.source_remove = GLib.source_remove
        GObject.GObject.__init__(self)
        XpraClientBase.__init__(self)

    def init(self, opts):
        XpraClientBase.init(self, opts)
        self.glib_init()

    def get_scheduler(self):
        return GLib


    def install_signal_handlers(self) -> None:
        from xpra.gtk.signals import install_signal_handlers
        install_signal_handlers("%s Client" % self.client_type(), self.handle_app_signal)


    def setup_connection(self, conn):
        protocol = super().setup_connection(conn)
        protocol._log_stats  = False
        GLib.idle_add(self.send_hello)
        return protocol


    def client_type(self) -> str:
        #overridden in subclasses!
        return "Python3/GObject"


    def init_packet_handlers(self) -> None:
        XpraClientBase.init_packet_handlers(self)
        def noop_handler(packet : PacketType) -> None:    # pragma: no cover
            log("ignoring packet: %s", packet)
        #ignore the following packet types without error:
        #(newer servers should avoid sending us any of those)
        for t in (
            "new-window", "new-override-redirect",
            "draw", "cursor", "bell",
            "notify_show", "notify_close",
            "ping", "ping_echo",
            "window-metadata", "configure-override-redirect",
            "lost-window",
            ):
            self.add_packet_handler(t, noop_handler, False)

    def run(self) -> ExitValue:
        XpraClientBase.run(self)
        self.run_loop()
        return self.exit_code or 0

    def run_loop(self) -> None:
        self.glib_mainloop = GLib.MainLoop()
        self.glib_mainloop.run()

    def make_hello(self) -> dict[str,Any]:
        capabilities = XpraClientBase.make_hello(self)
        capabilities["keyboard"] = False
        return capabilities

    def quit(self, exit_code:int|ExitCode=0) -> None:
        log("quit(%s) current exit_code=%s", exit_code, self.exit_code)
        if self.exit_code is None:
            self.exit_code = exit_code
        self.cleanup()
        GLib.timeout_add(50, self.exit_loop)

    def exit_loop(self) -> None:
        self.glib_mainloop.quit()
