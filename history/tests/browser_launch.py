"""Launch Chromium for browser tests without disabling its sandbox."""

import os
from pathlib import Path
import shutil


def launch_chromium(playwright):
    override = os.environ.get('PADLENS_CHROMIUM_PATH')
    if override:
        executable = Path(override).expanduser()
        if not executable.is_file():
            raise FileNotFoundError(f'PADLENS_CHROMIUM_PATH is not a file: {executable}')
        return playwright.chromium.launch(headless=True, chromium_sandbox=True,
                                          executable_path=str(executable))

    # Prefer the browser build matched to the installed Playwright version.
    if Path(playwright.chromium.executable_path).is_file():
        return playwright.chromium.launch(headless=True, chromium_sandbox=True)

    executable = shutil.which('chromium') or shutil.which('chromium.exe')
    if executable:
        return playwright.chromium.launch(headless=True, chromium_sandbox=True,
                                          executable_path=executable)

    # Let Playwright report the missing browser with its own diagnostic.
    return playwright.chromium.launch(headless=True, chromium_sandbox=True)
