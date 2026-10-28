#!/usr/bin/env python3
"""Build a reproducible, local-only PadLens preview archive with stdlib."""

from __future__ import annotations

import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import posixpath
import re
import struct
from urllib.parse import unquote, urlsplit
import zipfile


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "dist" / "PadLens-local-preview.zip"
STABLE_SHA256 = {
    "controller/controller_atlas.png": "7a887c052c689e3bdf77942929d9b8dc0af374274eb1e9c084a2161d89757e3d",
    "controller/controller_atlas_light.png": "274f521a31eaafbc370f04f18caabaf6d566c72f0cc47f39859c0e8a479b6797",
    "controller/controller_layout.json": "4ecf35f89bdc8d393bea3e50a2bdfe85c28e3c9942abc9f56b6676bdef1a9ad4",
    "history/input_history.html": "6e320952fa99d054828f0c7e8d57ad1b84fef4eff2f46873db2656653dc7e770",
    "history/overlay.js": "e167f3aab3735480ea657fc90725a81b03cdc420eb5fc0e1ad5eb619e77505fc",
    "history/history_core.js": "693e9ff908bd3c80d411cd1ed065c210e946b4de2eed9941adc1cce021b660e6",
    "history/user_config.js": "4c17875498e036f2b2c104dc46bfd9872d6620beeb65fc52671073fbc8758b84",
}
DOCUMENTS = (
    "LICENSE", "README.md", "README.ja.md", "SECURITY.md",
    "controller/README.md", "controller/README.ja.md",
    "history/README.md", "history/README.ja.md", "history/check_websocket.ps1",
    "docs/installation.md", "docs/installation.ja.md",
    "docs/architecture.md", "docs/architecture.ja.md",
    "docs/testing.md", "docs/testing.ja.md",
)
IMAGES = (
    "docs/images/controller-preview.png",
    "docs/images/history-preview.png",
    "docs/images/history-settings.png",
)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_files() -> dict[str, bytes]:
    names = sorted((*STABLE_SHA256, *DOCUMENTS, *IMAGES))
    result = {}
    for name in sorted(names):
        path = ROOT / name
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"Missing or linked package input: {name}")
        data = path.read_bytes()
        if name in STABLE_SHA256 and digest(data) != STABLE_SHA256[name]:
            raise ValueError(f"Stable source hash mismatch: {name}")
        result[name] = data
    return result


def png_size(data: bytes) -> tuple[int, int]:
    if data[:16] != b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR" or len(data) < 24:
        raise ValueError("Invalid PNG header")
    return struct.unpack(">II", data[16:24])


def check_relationships(files: dict[str, bytes]) -> None:
    html = files["history/input_history.html"].decode("utf-8")
    scripts = re.findall(r"<script\b[^>]*\bsrc=[\"']([^\"']+)[\"']", html, re.I)
    expected = {"user_config.js", "history_core.js", "overlay.js"}
    if len(scripts) != 3 or set(scripts) != expected:
        raise ValueError(f"Unexpected History script references: {scripts}")
    for name in scripts:
        if f"history/{name}" not in files:
            raise ValueError(f"Missing History script: {name}")

    layout = json.loads(files["controller/controller_layout.json"])
    sizes = {
        png_size(files["controller/controller_atlas.png"]),
        png_size(files["controller/controller_atlas_light.png"]),
    }
    if len(sizes) != 1:
        raise ValueError("Controller atlas dimensions differ")
    width, height = sizes.pop()
    if not layout.get("elements"):
        raise ValueError("Controller layout has no elements")
    for element in layout["elements"]:
        x, y, w, h = element["mapping"]
        if not (0 <= x and 0 <= y and w > 0 and h > 0 and x + w <= width and y + h <= height):
            raise ValueError(f"Controller mapping outside PNG: {element.get('id')}")


def check_local_link(name: str, target: str, files: dict[str, bytes]) -> None:
    """Check one local reference against the archive's root-relative names."""
    if re.match(r"^[A-Za-z]:[\\/]", target):
        raise ValueError(f"Absolute link in {name}: {target}")
    parsed = urlsplit(target)
    if parsed.scheme == "file":
        raise ValueError(f"Absolute link in {name}: {target}")
    if parsed.scheme or parsed.netloc or not parsed.path:
        return  # External URL or an anchor/query on this page.
    path = unquote(parsed.path)
    if path.startswith("/"):
        raise ValueError(f"Absolute link in {name}: {target}")
    resolved = posixpath.normpath(posixpath.join(posixpath.dirname(name), path))
    if resolved == ".." or resolved.startswith("../") or resolved not in files:
        raise ValueError(f"Broken or escaping link in {name}: {target}")


class MarkdownHTMLLinks(HTMLParser):
    """Collect image and anchor targets from HTML embedded in Markdown."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.targets: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attribute = {"img": "src", "a": "href"}.get(tag)
        if attribute is None:
            return
        values = dict(attrs)
        target = values.get(attribute)
        if tag == "img" and not target:
            raise ValueError("HTML image has no src")
        if target:
            self.targets.append(target)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)


def check_markdown_links(files: dict[str, bytes]) -> None:
    """Reject missing Markdown and embedded HTML targets in the archive."""
    link_pattern = re.compile(r"!?\[[^\]]*\]\((?:<([^>]+)>|([^\s)]+))(?:\s+[^)]*)?\)")
    for name, data in files.items():
        if not name.endswith(".md"):
            continue
        source = data.decode("utf-8")
        for match in link_pattern.finditer(source):
            check_local_link(name, match.group(1) or match.group(2), files)
        html_links = MarkdownHTMLLinks()
        html_links.feed(source)
        for target in html_links.targets:
            check_local_link(name, target, files)


def write_archive(files: dict[str, bytes]) -> None:
    OUTPUT.parent.mkdir(exist_ok=True)
    temporary = OUTPUT.with_suffix(".zip.tmp")
    try:
        with zipfile.ZipFile(temporary, "w") as archive:
            for name, data in sorted(files.items()):
                entry = zipfile.ZipInfo(f"PadLens/{name}", (1980, 1, 1, 0, 0, 0))
                entry.compress_type = zipfile.ZIP_DEFLATED
                entry.create_system = 3
                entry.external_attr = 0o100644 << 16
                archive.writestr(entry, data, compresslevel=9)
        with zipfile.ZipFile(temporary) as archive:
            expected = [f"PadLens/{name}" for name in sorted(files)]
            if archive.namelist() != expected or archive.testzip() is not None:
                raise ValueError("Archive contents or CRC check failed")
            extracted = {}
            for name, data in files.items():
                actual = archive.read(f"PadLens/{name}")
                if actual != data:
                    raise ValueError(f"Archive content mismatch: {name}")
                extracted[name] = actual
            check_relationships(extracted)
            check_markdown_links(extracted)
        temporary.replace(OUTPUT)
    finally:
        temporary.unlink(missing_ok=True)


def main() -> None:
    files = load_files()
    check_relationships(files)
    check_markdown_links(files)
    write_archive(files)
    print(f"Local preview only: {OUTPUT}")
    print(f"Files: {len(files)}")
    print(f"SHA-256: {digest(OUTPUT.read_bytes())}")


if __name__ == "__main__":
    main()
