#!/usr/bin/env python3
"""Bump version, rebuild, and twine-check artifacts.

Usage: scripts/release.py 0.1.6
"""

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PYPROJECT = ROOT / "pyproject.toml"
INIT = ROOT / "mcp_server" / "__init__.py"
README = ROOT / "README.md"

VERSION_PATTERN = re.compile(r'^version = "([0-9]+\.[0-9]+\.[0-9]+)"$', re.MULTILINE)
INIT_PATTERN = re.compile(r'^__version__ = "([0-9]+\.[0-9]+\.[0-9]+)"$', re.MULTILINE)


def set_version(path: Path, pattern: re.Pattern[str], version: str) -> None:
    text = path.read_text()
    if not pattern.search(text):
        raise SystemExit(f"Pattern not found in {path}")
    path.write_text(
        pattern.sub(lambda m: m.group(0).replace(m.group(1), version), text)
    )


def update_readme(version: str) -> None:
    text = README.read_text()
    text = re.sub(r"Release \d+\.\d+\.\d+", f"Release {version}", text)
    text = re.sub(r"v\d+\.\d+\.\d+", f"v{version}", text)
    README.write_text(text)


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True, cwd=ROOT)


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: scripts/release.py <version>")
    version = sys.argv[1]
    if not re.match(r"^\d+\.\d+\.\d+$", version):
        raise SystemExit("Version must look like 0.1.6")

    set_version(PYPROJECT, VERSION_PATTERN, version)
    set_version(INIT, INIT_PATTERN, version)
    update_readme(version)

    run([sys.executable, "-m", "build", "--no-isolation"])
    run([sys.executable, "-m", "twine", "check", "dist/*"])
    print(f"Version set to {version}. Artifacts rebuilt and checked.")


if __name__ == "__main__":
    main()
