import asyncio
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

UPSTREAM_REVISION = "47840a1bee8438324ff10753c4291148c46071c8"


@dataclass(frozen=True)
class DownloadResult:
    title: str
    note_id: str
    image_paths: tuple[Path, ...]
    source_url: str


def load_upstream(root: Path):
    root = Path(os.path.normpath(root.resolve()))
    if not (root / "source" / "__init__.py").is_file():
        raise RuntimeError("XHS-Downloader checkout not found; set XHS_DOWNLOADER_DIR")
    revision = subprocess.run(
        ["git", "-c", f"safe.directory={root.as_posix()}", "-C", str(root),
         "rev-parse", "HEAD"],
        capture_output=True, text=True, check=False,
    )
    if revision.stdout.strip() != UPSTREAM_REVISION:
        raise RuntimeError("XHS-Downloader checkout must use the revision in README.md")
    sys.path.insert(0, str(root))
    try:
        from source import XHS
    finally:
        sys.path.pop(0)
    return XHS


def ordered_images(folder: Path, expected: int) -> tuple[Path, ...]:
    indexed = {}
    for path in folder.iterdir():
        match = re.fullmatch(r".+_(\d+)", path.stem)
        if path.is_file() and match and path.stat().st_size:
            index = int(match[1])
            if index in indexed:
                raise RuntimeError(f"Duplicate downloaded image index {index}")
            indexed[index] = path
    for index in range(1, expected + 1):
        if index not in indexed:
            raise RuntimeError(f"Failed to download image {index}/{expected}")
    if len(indexed) != expected:
        raise RuntimeError("Unexpected image indices from XHS-Downloader")
    return tuple(indexed[index] for index in range(1, expected + 1))


async def _extract(xhs_factory, url, staging, cookie, proxy):
    async with xhs_factory(
        work_path=str(staging),
        folder_name="images",
        name_format="作品ID",
        download_record=False,
        record_data=False,
        video_download=False,
        live_download=False,
        language="zh_CN",
        proxy=proxy,
        proxy_download=bool(proxy),
    ) as xhs:
        # Upstream 2.8 disables TLS verification on both sessions by default.
        request_client = xhs.manager.request_client
        request_client.verify = True
        xhs.manager.download_client.verify = True
        if cookie:
            cookies = xhs.manager.cookie_str_to_dict(cookie)
            if not cookies:
                raise ValueError("Invalid Xiaohongshu Cookie; use the browser's Cookie header value")
            for name, value in cookies.items():
                request_client.cookies.set(name, value, domain=".xiaohongshu.com", secure=True)
        # Upstream partial files otherwise share a cache keyed by note ID.
        xhs.downloader.temp = staging / "partial"
        xhs.downloader.temp.mkdir()
        notes = await xhs.extract(url, download=True, check_record=False)
    if len(notes) != 1 or not notes[0] or not notes[0].get("作品ID"):
        raise RuntimeError("Failed to extract note; check the link, network or XHS_COOKIE")
    note = notes[0]
    if note["作品类型"] not in {"图文", "图集"}:
        raise RuntimeError("This note is not an image post")
    if not (urls := note["下载地址"]):
        raise RuntimeError("XHS-Downloader returned no image URLs")
    return DownloadResult(
        note["作品标题"] or "", note["作品ID"],
        ordered_images(staging / "images", len(urls)), url,
    )


def download(url: str, staging: Path, upstream: Path, cookie: str = "",
             proxy: str | None = None) -> DownloadResult:
    return asyncio.run(_extract(load_upstream(upstream), url, staging, cookie, proxy))
