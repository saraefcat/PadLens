# Architecture

[日本語](architecture.ja.md) · [PadLens](../README.md)

## Overview

PadLens has two independent display components: Controller Overlay and Input History. OBS Studio and the Input Overlay plugin must be installed separately. PadLens does not add a resident service.

## Component comparison

| Item | [Controller Overlay](../controller/README.md) | [Input History](../history/README.md) |
| --- | --- | --- |
| OBS source | Input Overlay | Browser |
| Input source | Input Overlay plugin | Input Overlay plugin WebSocket server |
| Display method | PNG atlas and JSON layout | HTML and JavaScript |
| WebSocket server | Not required | Required |

## Data flow

```text
Controller: Gamepad → Input Overlay plugin → Input Overlay source (PNG + JSON) → OBS display
History:    Gamepad → Input Overlay plugin → WebSocket → HTML + JavaScript → OBS Browser source
```

## How Controller Overlay works

| File | Role |
| --- | --- |
| `controller/controller_atlas.png` | Standard PNG atlas |
| `controller/controller_atlas_light.png` | Lighter transparency PNG atlas |
| `controller/controller_layout.json` | Maps logical inputs to image regions and display positions |

Both PNGs are 2048×1199px and use the same JSON.

- `controller/build_controller_overlay.py` generates images.
- `controller/verify_layout.py` checks image regions and layout.

Neither tool is required for normal use.

## How Input History works

| File | Role |
| --- | --- |
| `history/input_history.html` | Page opened in the OBS Browser source; loads the three scripts below |
| `history/user_config.js` | Default endpoint and display preferences |
| `history/history_core.js` | Event validation and history state |
| `history/overlay.js` | WebSocket connection, rendering, and settings UI |

The client connects to `ws://127.0.0.1:16899/` by default. History uses the plugin WebSocket server and does not require adding an Input Overlay source to OBS.

## Data storage

| Data | Storage | On Browser source reload |
| --- | --- | --- |
| Input rows | Browser memory | Cleared |
| Display preferences | `localStorage` | Saved values are read when available |

Saved preferences take precedence over defaults in `user_config.js`. Legacy preference keys are read for compatibility and migrated to current keys.

Displayed Δt is based on input event times, not when a game accepts the input.

## Communication and security

The client endpoint and the server bind address are separate settings.

- With History's default URL, configure the Input Overlay plugin server to listen on `127.0.0.1:16899`.
- WebSocket input data is not encrypted. Do not expose or forward the port outside the PC.

See the [security information](../SECURITY.md).

## Verification limits

- Operation is not guaranteed in every OBS environment.
- Browser tests with simulated events differ from checks with a physical gamepad in OBS.
- Not every Controller button has been exhaustively tested in OBS.
- History preference persistence after an OBS restart and WebSocket reconnection in OBS remain unverified.

For commands and coverage, see [testing](testing.md).
