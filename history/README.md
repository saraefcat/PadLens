# Input History

[日本語](README.ja.md) · [PadLens](../README.md)

## Overview

Input History lists recent gamepad input in an OBS Browser source. It uses the Input Overlay plugin's WebSocket server and can be used without Controller Overlay or an Input Overlay source. Install OBS Studio and the plugin separately.

## Previews

<p><a href="../docs/images/history-preview.png"><img src="../docs/images/history-preview.png" alt="Input History preview" width="200"></a> <a href="../docs/images/history-settings.png"><img src="../docs/images/history-settings.png" alt="Input History settings preview" width="200"></a></p>

These previews use simulated input. The left image shows the defaults with no saved preferences (header on, interval off); the right shows the settings panel. Click either image to open the original.

## Tested environment and recommended setup

| Item | Details |
| --- | --- |
| Operating systems used during development | Windows 10 / Windows 11 |
| Recommended OS for new users | Windows 11 |
| OBS Studio used for the display check | 33.0.0 (portable) |
| Input Overlay used for the display check | 5.1.2 |
| Recommended History Browser source size | 200px wide × 400px high |
| Default WebSocket endpoint | `127.0.0.1:16899` |

[Regular support for Windows 10 has ended](https://support.microsoft.com/en-us/windows/deployment/updates-lifecycle/windows-10-support-has-ended-on-october-14-2025), so it is not recommended for new installations. The 200×400px OBS source size is separate from the 240/260/300px width setting inside History. Other OBS and Input Overlay versions have not been verified.

## Included files

| File | Purpose | Distribution ZIP |
| --- | --- | --- |
| `input_history.html` | Page opened by the OBS Browser source | Included |
| `user_config.js` | Default connection and display settings | Included |
| `history_core.js` | Input events and history state | Included |
| `overlay.js` | WebSocket, rendering, and settings UI | Included |
| `check_websocket.ps1` | Optional read-only Windows listener check | Included |

The HTML and three JavaScript files are required for display. The diagnostic script is optional. Python, Node.js, and Playwright are not required for normal use.

## Installation

See the [detailed installation guide](../docs/installation.md).

1. Install OBS Studio and the Input Overlay plugin.
2. Open the Input Overlay plugin settings from OBS **Tools** and enable **WebSocket Server**.
3. Bind its server to `127.0.0.1:16899`. Restart OBS to apply the setting, outside a broadcast or recording.
4. Keep the downloaded and extracted `history/` directory intact.
5. Add an OBS **Browser** source with **Local file** set to `history/input_history.html`.
6. Set its size to 200px wide by 400px high.
7. Use **Interact** for the Browser source to open History settings and check whether gamepad input appears.

An Input Overlay source is not needed for History alone. If input does not appear, check the plugin's gamepad hook and whether Windows recognizes the gamepad.

## Display settings

In **Interact**, hover over the upper-right corner to reveal the settings button.

| Setting | Effect | Default in `user_config.js` |
| --- | --- | --- |
| History order | Newest input at the top or bottom | Top |
| Input interval Δt | Show time between history rows | Off |
| Header | Show title and connection status | On |
| Automatic expiry | Remove old rows after a set time | On (9 seconds) |
| Internal history width | Choose 240, 260, or 300px | 260px |

The clear button removes current history. It is an action, not a saved preference.

Display preferences are saved to browser `localStorage` when changed. Saved preferences take precedence over `user_config.js` defaults. Legacy keys are read and migrated to current keys without deleting the old keys. If browser storage is unavailable, changes do not persist. The default connection URL is `ws://127.0.0.1:16899/`.

## Main features

- Shows recent gamepad input and groups near-simultaneous presses into one row.
- Numbers rows from 01 to 999, then returns to 01.
- Limits the row count and excludes invalid events from display processing.

## Troubleshooting

| Symptom | First check |
| --- | --- |
| History page is missing | Browser source Local file path and the HTML plus three JavaScript files |
| WebSocket cannot connect | The plugin's WebSocket Server is enabled and listens on `127.0.0.1:16899`; `check_websocket.ps1` can check the Windows listener without changing settings |
| Connected, but no gamepad input | The plugin's gamepad hook and Windows gamepad recognition |
| Cannot open settings | OBS Browser source **Interact** and the upper-right hover button |
| Settings do not persist | Whether `localStorage` works in that Browser source; persistence after an OBS restart is unverified |
| Width or layout differs | Both the 200×400px OBS source and the 240/260/300px internal width |

See the [installation guide](../docs/installation.md) for further checks.

## Security

- Bind the WebSocket server to loopback, normally `127.0.0.1`. A client URL on loopback does not restrict the server's bind address.
- Avoid all-interface addresses such as `0.0.0.0` and `::`; do not expose the port externally.
- Disable unnecessary keyboard and mouse hooks.
- OBS administrator mode and disabling the browser sandbox are not required.

See the [security information](../SECURITY.md).

## Limitations

- Input rows live in browser memory and disappear on reload; display preferences use `localStorage`.
- Δt is calculated from input event times, not from when a game accepts an input.
- Browser tests use simulated WebSocket events. Exhaustive OBS inputs, real disconnection/reconnection, and settings persistence after an OBS restart remain unverified.

## License

PadLens original HTML and JavaScript are covered by the [MIT License](../LICENSE), `Copyright (c) 2026 saraefcat`. OBS Studio and Input Overlay are separate projects with their own licenses.
