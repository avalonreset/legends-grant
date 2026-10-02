"""US grant discovery, public evidence, and conservative reviewed qualification."""
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

try:
    __version__ = version("legends-grant-evidence")
except PackageNotFoundError:
    __version__ = (Path(__file__).resolve().parents[1] / "VERSION").read_text().strip()
