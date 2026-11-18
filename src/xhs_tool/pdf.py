from collections.abc import Sequence
from contextlib import ExitStack
from pathlib import Path
from tempfile import TemporaryDirectory

from PIL import Image, ImageOps


def generate_pdf(images: Sequence[Path], output: Path) -> None:
    if not images:
        raise ValueError("Cannot generate a PDF without images")

    with ExitStack() as stack:
        pages = []
        for path in images:
            try:
                with Image.open(path) as source, ImageOps.exif_transpose(source) as image:
                    if image.has_transparency_data:
                        with image.convert("RGBA") as rgba, rgba.getchannel("A") as alpha:
                            page = Image.new("RGB", rgba.size, "white")
                            stack.callback(page.close)
                            page.paste(rgba, mask=alpha)
                    else:
                        page = image.convert("RGB")
                        stack.callback(page.close)
                    pages.append(page)
            except (OSError, ValueError, Image.DecompressionBombError) as error:
                raise ValueError(f"Failed to convert image {path.name}: {error}") from error

        with TemporaryDirectory(prefix=".pdf-", dir=output.parent) as directory:
            temporary = Path(directory) / "pages.pdf"
            try:
                pages[0].save(
                    temporary, "PDF", save_all=True, append_images=pages[1:],
                    resolution=96, quality=95, subsampling=0,
                )
                temporary.replace(output)
            except OSError as error:
                raise OSError(f"Failed to write PDF {output.name}: {error}") from error
