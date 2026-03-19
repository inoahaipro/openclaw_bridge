"""
oclaw_bridge.py — OpenClaw transport layer for AutoJs6 accessibility bridge
Drop into your OpenClaw project root. Replaces ADB calls with localhost TCP.

Usage:
    from oclaw_bridge import Bridge, BridgeError
    b = Bridge()
    b.home()
    b.find_and_tap(text="Settings")
    print(b.get_screen_text())
"""

import socket
import json
import time

class BridgeError(Exception):
    pass

class Bridge:
    def __init__(self, host="127.0.0.1", port=9999, timeout=10):
        self.host    = host
        self.port    = port
        self.timeout = timeout

    def _call(self, action, params=None):
        payload = json.dumps({"action": action, "params": params or {}}) + "\n"
        try:
            with socket.create_connection((self.host, self.port), timeout=self.timeout) as s:
                s.sendall(payload.encode("utf-8"))
                buf = b""
                while True:
                    chunk = s.recv(65536)
                    if not chunk:
                        break
                    buf += chunk
                    if b"\n" in buf:
                        break
        except (ConnectionRefusedError, OSError) as e:
            raise BridgeError(f"Bridge unreachable at {self.host}:{self.port} — is AutoJs6 running? {e}")

        try:
            result = json.loads(buf.decode("utf-8").strip())
        except json.JSONDecodeError as e:
            raise BridgeError(f"Bad JSON from bridge: {e} — raw: {buf[:200]}")

        if not result.get("ok"):
            raise BridgeError(result.get("error", "unknown error"))

        return result.get("result")

    def _sel(self, text=None, text_contains=None, id=None, desc=None) -> dict:
        if text is not None:          return {"text": text}
        if text_contains is not None: return {"textContains": text_contains}
        if id is not None:            return {"id": id}
        if desc is not None:          return {"desc": desc}
        raise ValueError("At least one selector required: text, text_contains, id, or desc")

    # ── Screen reading ─────────────────────────────────────────────────────────

    def get_screen(self) -> dict:
        """Full accessibility node tree."""
        return self._call("getScreen")

    def get_screen_text(self) -> list:
        """Flat list of all visible text — cheapest for LLM context."""
        return self._call("getScreenText") or []

    def screenshot(self) -> str:
        """Base64-encoded PNG of current screen."""
        result = self._call("screenshot")
        return result["base64"]

    # ── Element finding ────────────────────────────────────────────────────────

    def find_and_tap(self, text=None, text_contains=None, id=None, desc=None) -> dict:
        """Find element by selector and tap it."""
        return self._call("findAndTap", self._sel(text, text_contains, id, desc))

    def find_all(self, text=None, text_contains=None, id=None, desc=None) -> list:
        """Return all matching elements as list of dicts."""
        return self._call("findAll", self._sel(text, text_contains, id, desc)) or []

    def wait_for(self, text=None, text_contains=None, id=None, desc=None, timeout=8000) -> dict:
        """Block until element appears. Returns bounds or raises BridgeError."""
        p = self._sel(text, text_contains, id, desc)
        p["timeout"] = timeout
        return self._call("waitFor", p)

    def wait_for_gone(self, text=None, text_contains=None, id=None, desc=None, timeout=8000):
        """Block until element disappears."""
        p = self._sel(text, text_contains, id, desc)
        p["timeout"] = timeout
        return self._call("waitForGone", p)

    def is_on_screen(self, text=None, text_contains=None, id=None, desc=None) -> bool:
        """Quick boolean check if element is visible."""
        return bool(self._call("isOnScreen", self._sel(text, text_contains, id, desc)))

    def get_bounds(self, text=None, text_contains=None, id=None, desc=None) -> dict:
        """Get coordinates without tapping. Returns left/top/right/bottom/cx/cy."""
        return self._call("getBounds", self._sel(text, text_contains, id, desc))

    def get_text_of(self, text=None, text_contains=None, id=None, desc=None) -> str:
        """Read text value of a specific element."""
        return self._call("getTextOf", self._sel(text, text_contains, id, desc))

    def is_enabled(self, text=None, text_contains=None, id=None, desc=None) -> bool:
        """Check if element is enabled."""
        return bool(self._call("isEnabled", self._sel(text, text_contains, id, desc)))

    def is_checked(self, text=None, text_contains=None, id=None, desc=None) -> bool:
        """Check if toggle/checkbox is checked."""
        return bool(self._call("isChecked", self._sel(text, text_contains, id, desc)))

    # ── Touch actions ──────────────────────────────────────────────────────────

    def tap_at(self, x: int, y: int):
        """Tap at absolute screen coordinates."""
        return self._call("tapAt", {"x": x, "y": y})

    def long_press(self, x=None, y=None, text=None, text_contains=None, id=None, desc=None):
        """Long press at coordinates or on element."""
        if x is not None and y is not None:
            return self._call("longPress", {"x": x, "y": y})
        return self._call("longPress", self._sel(text, text_contains, id, desc))

    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration: int = 300):
        """Swipe from (x1,y1) to (x2,y2)."""
        return self._call("swipe", {"x1": x1, "y1": y1, "x2": x2, "y2": y2, "duration": duration})

    def scroll(self, direction: str = "down"):
        """Scroll: up / down / left / right."""
        return self._call("scroll", {"direction": direction})

    # ── Text / clipboard ───────────────────────────────────────────────────────

    def type_text(self, text: str, field_id: str = None):
        """Type text into focused field. Optionally target by resource id."""
        p = {"text": text}
        if field_id:
            p["id"] = field_id
        return self._call("typeText", p)

    def clear_field(self):
        """Clear currently focused text field."""
        return self._call("clearField")

    def paste(self):
        """Paste clipboard into focused field."""
        return self._call("paste")

    def set_clipboard(self, text: str):
        """Write text to clipboard."""
        return self._call("setClipboard", {"text": text})

    def get_clipboard(self) -> str:
        """Read current clipboard text."""
        return self._call("getClipboard")

    def get_focused_text(self) -> str:
        """Read text value of currently focused input field."""
        return self._call("getFocusedText")

    # ── Keys ───────────────────────────────────────────────────────────────────

    def press_key(self, keycode: str):
        """Send a keycode via shell. Prefix KEYCODE_ is optional.
        Examples: 'ENTER', 'DEL', 'TAB', 'VOLUME_UP', 'WAKEUP', 'SLEEP'
        """
        return self._call("pressKey", {"keycode": keycode})

    # ── Navigation ─────────────────────────────────────────────────────────────

    def back(self):
        return self._call("back")

    def home(self):
        return self._call("home")

    def recents(self):
        return self._call("recents")

    def open_notifications(self):
        """Pull down notification shade via swipe."""
        return self._call("openNotifications")

    def close_notifications(self):
        """Collapse notification shade via swipe."""
        return self._call("closeNotifications")

    def wake_screen(self):
        """Wake screen if off."""
        return self._call("wakeScreen")

    def lock_screen(self):
        """Lock/sleep the screen."""
        return self._call("lockScreen")

    # ── App control ────────────────────────────────────────────────────────────

    def launch_app(self, package: str):
        """Launch app by package name."""
        return self._call("launchApp", {"package": package})

    def kill_app(self, package: str):
        """Force stop app via am force-stop (no root needed)."""
        return self._call("killApp", {"package": package})

    def get_current_app(self) -> dict:
        """Return { package, activity } of foreground app."""
        return self._call("getCurrentApp")

    def wait_for_app(self, package: str, timeout: int = 8000):
        """Block until specific app is in foreground."""
        return self._call("waitForApp", {"package": package, "timeout": timeout})

    def open_url(self, url: str):
        """Open URL in default browser."""
        return self._call("openUrl", {"url": url})

    # ── Device / system ────────────────────────────────────────────────────────

    def set_brightness(self, level: int):
        """Set screen brightness 0-255."""
        return self._call("setBrightness", {"level": level})

    def shell(self, cmd: str) -> dict:
        """Run a shell command. Returns { stdout, stderr, code }."""
        return self._call("shell", {"cmd": cmd})

    # ── Utility ────────────────────────────────────────────────────────────────

    def sleep(self, seconds: float):
        time.sleep(seconds)

    def is_alive(self) -> bool:
        """Check if bridge is reachable."""
        try:
            self.get_screen_text()
            return True
        except BridgeError:
            return False
