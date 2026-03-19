#!/usr/bin/env python

"""bridge_cli.py - Thin CLI wrapper around oclaw_bridge.Bridge

Usage examples (from Termux):
  python bridge_cli.py get-text
  python bridge_cli.py launch-app com.google.android.gm
  python bridge_cli.py tap-text "Connections"
  python bridge_cli.py tap-desc "Photo taken on Mar 18, 2026"
  python bridge_cli.py swipe 540 1900 540 400 400

Exit codes:
  0 on success, non-zero on BridgeError or bad usage.
"""

import sys
from oclaw_bridge import Bridge, BridgeError


def print_usage() -> None:
    print(
        "Usage: bridge_cli.py <command> [args...]\n\n"
        "Commands:\n"
        "  get-text                          # dump screen text (one line per entry)\n"
        "  get-tree                          # dump raw node tree (repr)\n"
        "  launch-app <package>              # launch app by package name\n"
        "  tap-text <substring>              # tap first element whose text contains substring\n"
        "  tap-desc <substring>              # tap first element whose content-desc contains substring\n"
        "  swipe <x1> <y1> <x2> <y2> [dur]   # swipe from (x1,y1) to (x2,y2)\n",
        file=sys.stderr,
    )


def main() -> int:
    if len(sys.argv) < 2:
        print_usage()
        return 1

    cmd, *args = sys.argv[1:]
    b = Bridge()

    try:
        if cmd == "get-text":
            lines = b.get_screen_text()
            for line in lines:
                print("-", line)
            return 0

        if cmd == "get-tree":
            tree = b.get_screen()
            # Simple repr; for heavy debugging you can switch to json.dumps here.
            print(tree)
            return 0

        if cmd == "launch-app":
            if not args:
                print("launch-app requires a package name", file=sys.stderr)
                return 2
            pkg = args[0]
            b.launch_app(pkg)
            return 0

        if cmd == "tap-text":
            if not args:
                print("tap-text requires a substring", file=sys.stderr)
                return 2
            sub = args[0]
            b.find_and_tap(text_contains=sub)
            return 0

        if cmd == "tap-desc":
            if not args:
                print("tap-desc requires a substring", file=sys.stderr)
                return 2
            sub = args[0]
            b.find_and_tap(desc=sub)
            return 0

        if cmd == "swipe":
            if len(args) < 4:
                print("swipe requires x1 y1 x2 y2 [duration_ms]", file=sys.stderr)
                return 2
            x1, y1, x2, y2 = map(int, args[:4])
            duration = int(args[4]) if len(args) >= 5 else 300
            b.swipe(x1, y1, x2, y2, duration=duration)
            return 0

        print("Unknown command:", cmd, file=sys.stderr)
        print_usage()
        return 1

    except BridgeError as e:
        print("BridgeError:", e, file=sys.stderr)
        return 10


if __name__ == "__main__":
    raise SystemExit(main())
