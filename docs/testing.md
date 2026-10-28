# Testing and verification

[日本語](testing.ja.md) · [PadLens](../README.md)

This page describes tests available from a source checkout and the limits of their coverage. Test tools are not required for normal PadLens use. See the [architecture](architecture.md) and [security information](../SECURITY.md).

## Test inventory

| Check | Purpose | Requirement and method | Coverage |
| --- | --- | --- | --- |
| History Node.js tests | Check input and display-setting logic | Run the `node --test` command below | 30 cases covering event validation, ordering, simultaneous presses, limits, and sequence numbers |
| JavaScript syntax | Check runtime-script syntax | Run the `node --check` commands below | Syntax only; not OBS rendering or communication |
| Chromium browser tests | Check History display and interaction | Run five Python files individually with Playwright and Chromium | Width, settings, simulated input, sequence, stress, and legacy preference migration; not OBS behavior |
| Controller image and layout | Check shipped PNG and JSON consistency | Run `controller/verify_layout.py` with Python and Pillow | PNG dimensions and transparency, 18 JSON elements; not physical button operation |
| Distribution ZIP | Check package contents and references | Run `scripts/package_release.py` with Python standard library | Stable hashes, HTML/Markdown references, CRC, reproducibility across two runs |
| Public snapshot | Check public-file extraction | Run `scripts/build_public_snapshot.py` with Python standard library | Allowlist, links, static sensitive-content checks, source hashes, reproducibility |

## Requirements

- **Normal use:** Requires OBS Studio and the Input Overlay plugin; not Node.js, Python, or Playwright.
- **Node.js tests and syntax checks:** Require Node.js.
- **Controller layout check:** Requires Python and Pillow. CairoSVG is needed only to regenerate images, not to check shipped PNGs.
- **Browser tests:** Require Python Playwright and matching Chromium. The recorded test environment used Python 3.12.14, Playwright 1.64.1, and Playwright-managed Chromium. These are not minimum supported versions.
- **ZIP and public snapshot:** Use the Python standard library.

## How to run tests

Run these Windows PowerShell commands from the **PadLens source root**. `python` means an installed Python interpreter. Test scripts and the public snapshot generator are not included in the distribution ZIP.

### Node.js and JavaScript syntax

```powershell
node --test history/tests/branding.test.js history/tests/hardening.test.js history/tests/history_core.test.js history/tests/layout_policy.test.js history/tests/test_sequence.test.js

node --check history/user_config.js
node --check history/history_core.js
node --check history/overlay.js
```

### Controller image and layout

```powershell
python -X utf8 controller/verify_layout.py
```

This needs Pillow, but does not start OBS or regenerate images.

### Chromium browser tests

For a first run, create an isolated environment from the source root. Python must already be installed. Playwright 1.64.1 is the version used for verification, not a claimed minimum. The virtual environment and managed browser stay under `.local/`; they do not modify your everyday browser profile or global Python environment.

```powershell
python -m venv .local/venv-playwright
New-Item -ItemType Directory -Force .local/playwright-browsers | Out-Null
$env:PLAYWRIGHT_BROWSERS_PATH = (Resolve-Path '.local/playwright-browsers').Path
$browserPython = (Resolve-Path '.local/venv-playwright/Scripts/python.exe').Path
& $browserPython -m pip install 'playwright==1.64.1'
& $browserPython -m playwright install chromium
```

With the environment ready, run the first four of five files individually. Activating the virtual environment is not necessary.

```powershell
$env:PLAYWRIGHT_BROWSERS_PATH = (Resolve-Path '.local/playwright-browsers').Path
$browserPython = (Resolve-Path '.local/venv-playwright/Scripts/python.exe').Path

$browserTests = @(
    'history/tests/test_browser.py'
    'history/tests/test_websocket_browser.py'
    'history/tests/test_stress_browser.py'
    'history/tests/test_sequence_browser.py'
)
foreach ($test in $browserTests) {
    & $browserPython $test
    if ($LASTEXITCODE -ne 0) {
        throw "$test failed (exit code $LASTEXITCODE)"
    }
}
```

The first four files use demo input or a simulated WebSocket. **The fifth, `test_branding_migration.py`, does not simulate WebSocket and attempts to connect to the default `127.0.0.1:16899`.** Check listeners without changing settings. If the check fails or a listener exists, do not run the fifth file.

```powershell
$checked = $false
$listeners = @()
try {
    $listeners = @(Get-NetTCPConnection -State Listen -ErrorAction Stop |
        Where-Object { $_.LocalPort -eq 16899 })
    $checked = $true
} catch {
    $checked = $false
}
if (-not $checked) {
    Write-Warning 'NOT RUN: Cannot read listener state; skipping the legacy preference migration test.'
} elseif ($listeners.Count -gt 0) {
    Write-Warning 'NOT RUN: Port 16899 has a listener; skipping the legacy preference migration test.'
} else {
    & $browserPython history/tests/test_branding_migration.py
    if ($LASTEXITCODE -ne 0) {
        throw "history/tests/test_branding_migration.py failed (exit code $LASTEXITCODE)"
    }
}
```

The browser launch helper enables Chromium sandboxing. Screenshots and other outputs go to `.local/browser-tests/`.

### Distribution ZIP and public snapshot

```powershell
python scripts/package_release.py
python scripts/build_public_snapshot.py
```

The ZIP is written to `dist/PadLens-local-preview.zip` and the snapshot to `.local/public-staging/PadLens/`. Both scripts check contents and display SHA-256 values. Run each twice with unchanged inputs and compare the hashes. The snapshot generator refuses to overwrite a manually changed snapshot.

## Verified scope

- All 30 History Node.js tests and five Chromium browser test files passed in the recorded verification environment. The Node.js command above was also rerun and passed 30 cases.
- Chromium checks used simulated input for display, settings, a 200×400px layout, and sequence rollover from 999 to 01. Simulated WebSocket checks exercise browser-side handling; they do not guarantee connections or reconnections to a production Input Overlay server.
- A display smoke test using PadLens files was performed with OBS Studio 33.0.0 portable and Input Overlay 5.1.2. This is distinct from exhaustive testing on physical hardware.

## Unverified areas and limits

- Every Controller button has not been exhaustively operated in OBS.
- History preference persistence after an OBS restart and real WebSocket disconnection/reconnection remain unverified.
- Browser tests use an in-memory `localStorage` substitute; they do not establish persistence after closing the browser or restarting OBS.
- The automatic-expiry setting was exercised, but time-based removal has not been verified in a real browser.
- Static checks and simulated-event tests do not guarantee operation in every OBS environment.

## Safe testing

- Do not change production OBS scenes or broadcast settings. Use a test scene for hardware checks.
- Do not use a production Input Overlay server as a test target without authorization, or use a personal browser profile.
- Do not disable the Chromium sandbox.
- Keep generated test outputs under unpublished paths such as `.local/` and `dist/`. Do not log credentials or actual keystrokes.
