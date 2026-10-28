# Installation

[日本語](installation.ja.md) · [PadLens](../README.md)

## Overview

Controller Overlay shows current gamepad input in an OBS **Input Overlay source**. Input History lists recent input in an OBS **Browser source**. You can install either component independently.

## Requirements

Install [OBS Studio](https://obsproject.com/) and the [Input Overlay plugin](https://github.com/univrsal/input-overlay) separately; PadLens does not bundle them. See the plugin's [official installation guide](https://github.com/univrsal/input-overlay/wiki/Installation).

| Item | Details |
| --- | --- |
| Operating systems used during development | Windows 10 / Windows 11 |
| Recommended OS for new users | Windows 11 |
| OBS Studio used for the display check | 33.0.0 (portable) |
| Input Overlay used for the display check | 5.1.2 |

- Display was checked with the OBS Studio and Input Overlay combination in the table. Development on two operating systems does not mean every operation was verified on both.
- Every operation and other software versions remain unverified.
- [Regular support for Windows 10 has ended](https://support.microsoft.com/en-us/windows/deployment/updates-lifecycle/windows-10-support-has-ended-on-october-14-2025); Windows 11 is recommended for new installations.

## Obtain and extract files

Obtain and extract the PadLens source from GitHub or a PadLens distribution ZIP.

- Keep the `controller/` and `history/` directory structure. You do not need to move PNG, JSON, HTML, or JavaScript files individually.
- The distribution ZIP does not include developer scripts.
- Start in an OBS test scene to protect existing broadcast scenes.

## Controller Overlay

1. Add an **Input Overlay source** from the OBS Sources list. See the plugin's [official usage guide](https://github.com/univrsal/input-overlay/wiki/Usage).
2. In the source properties, select this PNG and JSON combination from `controller/`:

   | Appearance | PNG | JSON |
   | --- | --- | --- |
   | Standard | `controller_atlas.png` | `controller_layout.json` |
   | Lighter transparency | `controller_atlas_light.png` | `controller_layout.json` |
   | Sara | `controller_atlas_sara.png` | `controller_layout_sara.json` |
   | Sara RTA | `controller_atlas_sara_rta.png` | `controller_layout_sara.json` |

3. Select the gamepad in the Input Overlay source.
4. Use the gamepad and check that the display responds.

- If it does not respond, check the gamepad hook in the Input Overlay **plugin settings** under OBS **Tools**.
- **Controller alone does not need the WebSocket server.** Sara has cat-ear LB/RB, oval LT/RT indicators, paw-print sticks, eye-shaped View/Menu controls, and a nose-and-mouth HOME control. Sara's OBS rendering remains unverified.

See the [Controller guide](../controller/README.md) for features and limitations.

## Input History

History uses a **Browser source**. You do not need to add an Input Overlay source.

1. Open the Input Overlay **plugin settings** from OBS **Tools**.
2. Enable **WebSocket Server** and set its bind address to `127.0.0.1` and port to `16899`.
3. Restart OBS to apply the setting when you are not broadcasting or recording.
4. Add a **Browser source** from the OBS Sources list.
5. Enable **Local file** and select `history/input_history.html`.
6. Set the Browser source to 200px wide and 400px high.
7. Open **Interact** for the Browser source, then hover over the upper-right corner of the History page to reveal the settings button.
8. Use the gamepad and check that input appears in the history.

- 200×400px is the recommended OBS Browser source size for History.
- 240/260/300px are internal History display-width options.

See the [History guide](../history/README.md) for settings and features.

## Troubleshooting

| Symptom | First check |
| --- | --- |
| Controller image is missing | The matching PNG and JSON selected in the Input Overlay source properties |
| Controller buttons do not respond | Gamepad selection in the source and the gamepad hook in the plugin settings |
| History page is missing | Browser source Local file path and the intact `history/` directory |
| History WebSocket cannot connect | Server enabled and listening on `127.0.0.1:16899` in the plugin settings; `history/check_websocket.ps1` provides a read-only Windows listener check |
| WebSocket connects but input does not appear | The plugin's gamepad hook and Windows gamepad recognition |
| Cannot open History settings | Browser source **Interact** and the upper-right hover button |

See the [Controller guide](../controller/README.md) and [History guide](../history/README.md) for more detail.

## Security

- Configure the WebSocket server to listen on loopback, normally `127.0.0.1`. Setting only the History client endpoint to loopback does not limit the server's bind address.
- Avoid all-interface listeners such as `0.0.0.0` and `::`; do not expose the port externally.
- Disable unnecessary keyboard and mouse hooks.
- OBS administrator mode and disabling the browser sandbox are not required.

See [SECURITY.md](../SECURITY.md).
