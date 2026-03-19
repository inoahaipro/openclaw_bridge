# openclaw-bridge

Android accessibility bridge for OpenClaw.

This project wires together:

- **openclaw-bridge.js** (in AutoJs6 on the phone)
  - Runs as an accessibility-driven TCP server on `127.0.0.1:9999`
  - Exposes actions like `getScreen`, `getScreenText`, `findAndTap`, `tapAt`,
    `swipe`, `typeText`, `launchApp`, `openUrl`, `shell`, etc.

- **`oclaw_bridge.py`** (Python client)
  - Small transport layer that speaks the JSON line protocol to the AutoJs6
    server over localhost TCP.
  - Provides a typed `Bridge` class with methods like:
    - `get_screen()`, `get_screen_text()`
    - `find_and_tap(...)`, `tap_at(...)`, `swipe(...)`
    - `type_text(...)`, `press_key(...)`
    - `launch_app(...)`, `open_url(...)`, `shell(...)`, etc.

- **`bridge_cli.py`** (CLI wrapper)
  - Thin command-line interface around `Bridge` for use from Termux and
    OpenClaw exec hooks.
  - Example commands:

    ```bash
    # Dump screen text
    python bridge_cli.py get-text

    # Launch an app by package name
    python bridge_cli.py launch-app com.anthropic.claude

    # Tap first node whose text contains the given substring
    python bridge_cli.py tap-text "Connections"

    # Tap by contentDescription (e.g. newest photo in Google Photos)
    python bridge_cli.py tap-desc "Photo taken on Mar 18, 2026"

    # Swipe from (x1,y1) to (x2,y2)
    python bridge_cli.py swipe 540 1900 540 400 400
    ```

The goal is to replace raw ADB + uiautomator hacks with a clean, scriptable
"hands" API that OpenClaw (or any other agent) can call to drive the Android
device: opening apps, tapping UI, asking other AIs (Claude), sharing photos,
composing emails, etc.

## Status

- Core bridge protocol and Python client are working.
- CLI wrapper is usable for:
  - launching apps
  - reading screen text
  - tapping by text or contentDescription
  - swiping
- Higher-level flows (Photos → Gmail, Claude app automation, Settings
  navigation) are being iterated and will likely grow into their own CLI
  subcommands.

## Requirements

- AutoJs6 (or similar) on the Android device, running `openclaw-bridge.js` as an
  accessibility service on port 9999.
- Python 3 in Termux on the same device.

## License

See [LICENSE](LICENSE).
