#!/usr/bin/env python3
# This file is part of Xpra.
# Copyright (C) 2010 Nathaniel Smith <njs@pobox.com>
# Copyright (C) 2011-2023 Antoine Martin <antoine@xpra.org>
# Xpra is released under the terms of the GNU GPL v2, or, at your option, any
# later version. See the file COPYING for details.

from xpra.platform import platform_import

#default:
Keyboard : type | None = None

platform_import(globals(), "keyboard", True,
                "Keyboard")

def main():
    import sys
    from xpra.os_util import WIN32, OSX, POSIX
    from xpra.util.str_fn import bytestostr
    from xpra.util.str_fn import print_nested_dict
    from xpra.util.str_fn import csv
    from xpra.platform import program_context
    from xpra.log import enable_color, enable_debug_for
    with program_context("Keyboard-Tool", "Keyboard Tool"):
        #use the logger for the platform module we import from
        enable_color()
        verbose = "-v" in sys.argv or "--verbose" in sys.argv or \
            (WIN32 and not ("-q" in sys.argv or "--quiet"))
        if verbose:
            enable_debug_for("keyboard")

        #naughty, but how else can I hook this up?
        if POSIX and not OSX:
            try:
                from xpra.x11.bindings.posix_display_source import init_posix_display_source
                init_posix_display_source()
            except Exception as e:
                print("failed to connect to the X11 server:")
                print(" %s" % e)
                #hope for the best..

        if not Keyboard:
            print("no keyboard implementation")
            return 1
        keyboard = Keyboard()  #pylint: disable=not-callable
        mod_meanings, mod_managed, mod_pointermissing = keyboard.get_keymap_modifiers()
        print("Modifiers:")
        print_nested_dict(mod_meanings)
        print("")
        print("Server Managed                    : %s" % (csv(mod_managed) or "None"))
        print("Missing from pointer events       : %s" % (csv(mod_pointermissing) or "None"))
        print("")
        layout,layouts,variant,variants, options = keyboard.get_layout_spec()
        print("Layout:     '%s'" % bytestostr(layout or b""))
        print("Layouts:    %s" % csv("'%s'" % bytestostr(x) for x in (layouts or [])))
        print("Variant:    '%s'" % bytestostr(variant or b""))
        print("Variants:   %s" % csv("'%s'" % bytestostr(x) for x in (variants or [])))
        print("Options:    %s" % (options, ))
        print("")
        print("Repeat:     %s" % csv(keyboard.get_keyboard_repeat()))
        if verbose and POSIX:
            keysyms = keyboard.get_x11_keymap()
            if keysyms:
                print("Keysyms:")
                for keycode,keysyms in keysyms.items():
                    print(" %3i    : %s" % (keycode, csv(keysyms)))
    return 0


if __name__ == "__main__":
    main()
