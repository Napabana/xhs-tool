from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import urlsplit

from .downloader import DownloadResult, download
from .pdf import generate_pdf
from .utils import reserve_directory


def run(url: str, output: Path, upstream: Path, cookie: str = "",
        proxy: str | None = None, *, mode: str = "images") -> DownloadResult:
    if mode not in {"images", "pdf"}:
        raise ValueError(f"Unsupported mode: {mode}")
    parsed = urlsplit(url)
    if (
        parsed.scheme not in {"http", "https"}
        or parsed.netloc.lower() not in {
            "www.xiaohongshu.com", "xiaohongshu.com", "xhslink.com", "xhslink.cn",
        }
        or not parsed.path.strip("/")
        or any(char.isspace() for char in url)
    ):
        raise ValueError("Invalid Xiaohongshu URL")
    host = parsed.netloc.lower()
    if host == "xiaohongshu.com":
        host = "www.xiaohongshu.com"
    note_url = parsed._replace(scheme="https", netloc=host).geturl()

    output.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=".xhs-", dir=output) as temporary:
        staging = Path(temporary)
        result = download(note_url, staging, upstream, cookie, proxy)
        ready = staging / "images-ready"
        ready.mkdir()
        names = []
        for index, path in enumerate(result.image_paths, 1):
            name = f"{index:03d}{path.suffix.lower()}"
            path.rename(ready / name)
            names.append(name)
        target = reserve_directory(output, result.title or result.note_id)
        pdf = target / f"{target.name}.pdf"
        try:
            if mode == "pdf":
                generate_pdf([ready / name for name in names], pdf)
            ready.rename(target / "images")
        except (OSError, ValueError):
            if mode == "pdf":
                pdf.unlink(missing_ok=True)
            target.rmdir()
            raise
    return replace(
        result, source_url=url,
        image_paths=tuple(target / "images" / name for name in names),
    )
