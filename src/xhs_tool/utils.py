import re
from itertools import count
from pathlib import Path, PureWindowsPath


def sanitize_filename(title: str) -> str:
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", title).strip()
    name = name[:60].rstrip(" .") or "untitled"
    if PureWindowsPath(name).is_reserved():
        name = f"_{name}"
    return name


def reserve_directory(root: Path, title: str) -> Path:
    name = sanitize_filename(title)
    for number in count(1):
        path = root / (name if number == 1 else f"{name} ({number})")
        try:
            path.mkdir()
        except FileExistsError:
            continue
        return path
