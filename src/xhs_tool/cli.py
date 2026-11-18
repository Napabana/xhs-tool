import argparse
import os
from pathlib import Path

from .pipeline import run


def main() -> int:
    parser = argparse.ArgumentParser(description="Download Xiaohongshu images and optionally generate a PDF.")
    parser.add_argument("url")
    parser.add_argument("--mode", choices=["images", "pdf"], default="images")
    parser.add_argument("--output", type=Path, default=Path("output"))
    credentials = parser.add_mutually_exclusive_group()
    credentials.add_argument("--cookie")
    credentials.add_argument("--cookie-file", type=Path)
    parser.add_argument("--proxy")
    args = parser.parse_args()
    try:
        cookie = (
            args.cookie_file.read_text(encoding="utf-8-sig").strip()
            if args.cookie_file else args.cookie or os.environ.get("XHS_COOKIE", "")
        )
        result = run(
            args.url, args.output,
            Path(os.environ.get("XHS_DOWNLOADER_DIR", "../upstream-phase1")),
            cookie, args.proxy or os.environ.get("XHS_PROXY"), mode=args.mode,
        )
    except (ValueError, OSError, RuntimeError, ImportError) as error:
        parser.exit(1, f"xhs-tool: {error}\nNo note directory published. Retry after fixing the error.\n")
    images = result.image_paths[0].parent.resolve()
    print(f"Downloaded {len(result.image_paths)} images to {images}")
    if args.mode == "pdf":
        print(f"Generated {images.parent / (images.parent.name + '.pdf')}")
    return 0
