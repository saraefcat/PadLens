# PadLens

[日本語](README.ja.md)

## Overview

PadLens displays current and recent gamepad input in [OBS Studio](https://obsproject.com/) using the separately installed [Input Overlay plugin](https://github.com/univrsal/input-overlay). Its two components can be used independently. PadLens is not an official OBS Studio or Input Overlay product.

## Previews

**Controller Overlay** shows current input on a translucent controller. A standard and a lighter transparency PNG are available.

<a href="docs/images/controller-preview.png"><img src="docs/images/controller-preview.png" alt="Controller on a synthetic background" width="600"></a>

**Input History** lists recent inputs. The left image shows the defaults with no saved preferences; the right image shows the settings panel.

<p><a href="docs/images/history-preview.png"><img src="docs/images/history-preview.png" alt="Simulated input history with default settings" width="200"></a> <a href="docs/images/history-settings.png"><img src="docs/images/history-settings.png" alt="Input History settings panel" width="200"></a></p>

Click an image to open the original. These are previews with simulated inputs, not captures of a live broadcast.

## Two components

| Component | Displays | OBS source | Input Overlay WebSocket server |
| --- | --- | --- | --- |
| [Controller Overlay](controller/README.md) | Current buttons, triggers, and sticks | Input Overlay | Not required |
| [Input History](history/README.md) | Recent input, simultaneous presses, sequence numbers, and intervals | Browser | Required |

## Tested environment and recommended setup

Display was checked with OBS Studio 33.0.0 portable and Input Overlay 5.1.2. The operating systems used during development are a separate fact; not every operation was verified on both. Other operating systems and versions are not guaranteed. Install OBS Studio and Input Overlay separately.

| Item | Details |
| --- | --- |
| Operating systems used during development | Windows 10 / Windows 11 |
| Recommended OS for new users | Windows 11 |
| OBS Studio used for the display check | 33.0.0 (portable) |
| Input Overlay used for the display check | 5.1.2 |
| Recommended History browser source size | 200px wide × 400px high |
| History WebSocket endpoint | `127.0.0.1:16899` |

[Regular support for Windows 10 has ended](https://support.microsoft.com/en-us/windows/deployment/updates-lifecycle/windows-10-support-has-ended-on-october-14-2025), so it is not recommended for new installations.

## Quick start

See the [installation guide](docs/installation.md) for detailed steps. Start in an OBS test scene.

**Controller Overlay**

1. Add an **Input Overlay** source in OBS.
2. In that source, select a PNG and JSON from `controller/`:

   | Appearance | PNG | JSON |
   | --- | --- | --- |
   | Standard | `controller_atlas.png` | `controller_layout.json` |
   | Lighter transparency | `controller_atlas_light.png` | `controller_layout.json` |

3. Select the gamepad in the Input Overlay source. If input does not appear, check the gamepad hook in the Input Overlay plugin settings. Controller alone does not need the History WebSocket server.

**Input History**

1. Open the Input Overlay plugin settings from OBS **Tools**. Enable **WebSocket Server** and bind it to `127.0.0.1:16899`. Restart OBS outside a broadcast to apply the setting.
2. Keep the `history/` directory intact after obtaining the GitHub source or PadLens ZIP.
3. Add a **Browser** source. Enable **Local file**, select `history/input_history.html`, and set the source to 200px wide by 400px high.
4. Use OBS **Interact** for the Browser source to open History settings and check whether gamepad input appears.

If input does not appear, check the plugin's gamepad hook and whether Windows recognizes the gamepad. History does not require an Input Overlay source.

## Troubleshooting

| Symptom | First check |
| --- | --- |
| Controller image is missing | The Input Overlay source points to a PNG and the shared JSON in `controller/` |
| Buttons do not respond | The plugin's gamepad hook and the device selected in the Input Overlay source |
| History cannot connect | The plugin WebSocket server is enabled and listens on `127.0.0.1:16899` |
| History is blank | The HTML and three JavaScript files remain together in `history/` |

See the [installation guide](docs/installation.md) for more checks.

## Security

- Bind the WebSocket server to loopback and do not expose its port externally.
- Disable keyboard and mouse hooks if gamepad display does not need them.
- Administrator mode for OBS and disabling the browser sandbox are not required.

See [SECURITY.md](SECURITY.md).

## License

PadLens original code, tests, documentation, Controller PNG images, and HOME pictogram are covered by the [MIT License](LICENSE), `Copyright (c) 2026 saraefcat`. OBS Studio and Input Overlay are separate projects.
