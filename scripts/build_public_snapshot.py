#!/usr/bin/env python3
"""Build the public PadLens file tree from an explicit source allowlist.

Only the development checkout is editable. A manifest outside the public tree
guards a previously generated snapshot from accidental replacement after edits.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import uuid

from package_release import SARA_SHA256, STABLE_SHA256, check_markdown_links, digest


ROOT = Path(__file__).resolve().parents[1]
STAGING_ROOT = ROOT / ".local" / "public-staging"
TARGET = STAGING_ROOT / "PadLens"
MANIFEST = STAGING_ROOT / "manifest.json"
PUBLIC_FILES = (
    ".gitignore",
    "LICENSE",
    "README.md",
    "README.ja.md",
    "SECURITY.md",
    "controller/README.md",
    "controller/README.ja.md",
    "controller/build_controller_overlay.py",
    "controller/build_sara_overlay.py",
    "controller/controller_atlas.png",
    "controller/controller_atlas_light.png",
    "controller/controller_atlas_sara.png",
    "controller/controller_atlas_sara_rta.png",
    "controller/controller_layout.json",
    "controller/controller_layout_sara.json",
    "controller/verify_layout.py",
    "controller/verify_sara_layout.py",
    "history/README.md",
    "history/README.ja.md",
    "history/check_websocket.ps1",
    "history/history_core.js",
    "history/input_history.html",
    "history/overlay.js",
    "history/user_config.js",
    "history/tests/branding.test.js",
    "history/tests/browser_launch.py",
    "history/tests/hardening.test.js",
    "history/tests/history_core.test.js",
    "history/tests/layout_policy.test.js",
    "history/tests/test_branding_migration.py",
    "history/tests/test_browser.py",
    "history/tests/test_sequence.test.js",
    "history/tests/test_sequence_browser.py",
    "history/tests/test_stress_browser.py",
    "history/tests/test_websocket_browser.py",
    "docs/architecture.md",
    "docs/architecture.ja.md",
    "docs/images/controller-preview.png",
    "docs/images/history-preview.png",
    "docs/images/history-settings.png",
    "docs/installation.md",
    "docs/installation.ja.md",
    "docs/testing.md",
    "docs/testing.ja.md",
    "scripts/build_public_snapshot.py",
    "scripts/package_release.py",
)
# These checks are a release guard, not a substitute for reviewing source and
# images. Keep matches out of diagnostics so a rejected secret is not logged.
SENSITIVE_PATTERNS = {
    "Windows user path": re.compile(
        r"(?i)\b[A-Z]:[\\/](?:Users|Documents and Settings)[\\/](?P<user>[^\\/\s]{2,})[\\/]"
    ),
    "Unix user path": re.compile(r"(?<![\w/])/(?:home|Users)/(?P<user>[A-Za-z0-9._-]{2,})/"),
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |ENCRYPTED )?PRIVATE KEY-----"),
    "GitHub token": re.compile(
        r"(?<![A-Za-z0-9_])(?:gh[pousr]_|github_pat_)[A-Za-z0-9_.-]{20,}"
    ),
    "AWS access key ID": re.compile(r"(?<![A-Z0-9])(?:AKIA|ASIA)[A-Z0-9]{16}(?![A-Z0-9])"),
    "service token": re.compile(r"(?<![A-Za-z0-9])sk-[A-Za-z0-9_-]{20,}"),
    "authorization header": re.compile(
        r"(?i)\bAuthorization\s*[:=]\s*[\"']?(?:Bearer|Basic)\s+[A-Za-z0-9._~+/-]{20,}"
    ),
    "credentials in URL": re.compile(
        r"(?i)\b(?:https?|postgres(?:ql)?|mysql|mongodb(?:\+srv)?)://[^\s/:@]+:[^\s/@]+@"
    ),
}
CREDENTIAL_ASSIGNMENT = re.compile(
    r"(?i)\b[A-Za-z0-9_]*(?:password|passwd|api[_-]?key|secret|token)[A-Za-z0-9_]*"
    r"\s*[:=]\s*([\"'])([^\"'\r\n]{8,})\1"
)
PLACEHOLDER_PARTS = ("example", "sample", "placeholder", "your_", "changeme", "dummy", "<", "${")
GENERIC_USER_NAMES = {"public", "default", "shared", "example", "username", "yourname"}


def sensitive_findings(source: str) -> list[str]:
    """Return finding categories without returning or printing matched values."""
    findings = []
    for category, pattern in SENSITIVE_PATTERNS.items():
        if category.endswith("user path"):
            if any(match.group("user").lower() not in GENERIC_USER_NAMES
                   for match in pattern.finditer(source)):
                findings.append(category)
        elif pattern.search(source):
            findings.append(category)
    for match in CREDENTIAL_ASSIGNMENT.finditer(source):
        value = match.group(2).lower()
        if not any(part in value for part in PLACEHOLDER_PARTS):
            findings.append("hardcoded credential")
            break
    return findings


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def tree_hash(hashes: dict[str, str]) -> str:
    lines = "".join(f"{name}\0{hashes[name]}\n" for name in sorted(hashes))
    return sha256(lines.encode("utf-8"))


def assert_inside_staging(path: Path) -> None:
    if path.resolve() == STAGING_ROOT.resolve() or not path.resolve().is_relative_to(STAGING_ROOT.resolve()):
        raise ValueError(f"Refusing to move or delete outside staging: {path}")


def read_sources() -> tuple[dict[str, bytes], dict[str, str]]:
    if len(PUBLIC_FILES) != len(set(PUBLIC_FILES)):
        raise ValueError("Duplicate path in public allowlist")
    files = {}
    for name in PUBLIC_FILES:
        relative = Path(name)
        if relative.is_absolute() or ".." in relative.parts or "\\" in name:
            raise ValueError(f"Unsafe public path: {name}")
        path = ROOT / relative
        if not path.resolve().is_relative_to(ROOT) or not path.is_file():
            raise ValueError(f"Missing or escaping source file: {name}")
        if any(part.is_symlink() for part in (path, *path.parents) if part != ROOT):
            raise ValueError(f"Linked source path: {name}")
        data = path.read_bytes()
        expected_hash = STABLE_SHA256.get(name, SARA_SHA256.get(name))
        if expected_hash is not None and digest(data) != expected_hash:
            raise ValueError(f"Source hash mismatch: {name}")
        files[name] = data
    check_markdown_links(files)
    for name, data in files.items():
        if name == ".gitignore" or name.endswith((".md", ".py", ".js", ".html", ".json", ".ps1")):
            findings = sensitive_findings(data.decode("utf-8"))
            if findings:
                raise ValueError(f"Potential sensitive content in {name}: {', '.join(findings)}")
    return files, {name: sha256(data) for name, data in files.items()}


def inspect_tree(directory: Path) -> dict[str, str]:
    assert_inside_staging(directory)
    result = {}
    for path in directory.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"Linked public output: {path}")
        if path.is_file():
            name = path.relative_to(directory).as_posix()
            result[name] = sha256(path.read_bytes())
    return result


def write_manifest(hashes: dict[str, str]) -> None:
    payload = json.dumps({"files": hashes, "tree_sha256": tree_hash(hashes)},
                         indent=2, sort_keys=True) + "\n"
    temporary = STAGING_ROOT / f".manifest-{uuid.uuid4().hex}.tmp"
    temporary.write_text(payload, encoding="utf-8")
    os.replace(temporary, MANIFEST)


def previous_hashes() -> dict[str, str]:
    if not MANIFEST.is_file():
        raise ValueError("Existing public snapshot has no generator manifest")
    record = json.loads(MANIFEST.read_text(encoding="utf-8"))
    hashes = record["files"]
    if tree_hash(hashes) != record["tree_sha256"] or inspect_tree(TARGET) != hashes:
        raise ValueError("Existing public snapshot differs from its manifest")
    return hashes


def main() -> None:
    files, expected = read_sources()
    STAGING_ROOT.mkdir(parents=True, exist_ok=True)
    if TARGET.exists():
        previous_hashes()

    # Path.mkdir inherits the staging ACL. tempfile.mkdtemp creates an owner-only
    # directory on Windows, which would make the public output unreadable to the
    # workspace owner after the directory is renamed into place.
    temporary = STAGING_ROOT / f".PadLens-next-{uuid.uuid4().hex}"
    temporary.mkdir()
    assert_inside_staging(temporary)
    try:
        for name, data in files.items():
            destination = temporary / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
        if inspect_tree(temporary) != expected:
            raise ValueError("Copied public files differ from source hashes")
        check_markdown_links({name: (temporary / name).read_bytes() for name in expected})

        if TARGET.exists() and inspect_tree(TARGET) == expected:
            print("Public snapshot already matches source")
        elif TARGET.exists():
            old = STAGING_ROOT / f".PadLens-old-{uuid.uuid4().hex}"
            assert_inside_staging(old)
            TARGET.rename(old)
            try:
                temporary.rename(TARGET)
                write_manifest(expected)
            except Exception:
                if TARGET.exists():
                    failed = STAGING_ROOT / f".PadLens-failed-{uuid.uuid4().hex}"
                    assert_inside_staging(failed)
                    TARGET.rename(failed)
                    old.rename(TARGET)
                    shutil.rmtree(failed)
                else:
                    old.rename(TARGET)
                raise
            shutil.rmtree(old)
        else:
            temporary.rename(TARGET)
            try:
                write_manifest(expected)
            except Exception:
                assert_inside_staging(TARGET)
                shutil.rmtree(TARGET)
                raise
    finally:
        if temporary.exists():
            assert_inside_staging(temporary)
            shutil.rmtree(temporary)

    print(f"Public snapshot: {TARGET}")
    print(f"Files: {len(expected)}")
    print(f"Tree SHA-256: {tree_hash(expected)}")


if __name__ == "__main__":
    main()
