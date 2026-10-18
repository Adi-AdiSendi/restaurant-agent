"""Download a candidate once, crop it to 4:3 and write the WebP sizes the UI loads."""

import base64
import io
import re
import time
import urllib.request
from pathlib import Path

from PIL import Image

from scripts.photos.openverse import USER_AGENT, Candidate

CACHE = Path(__file__).resolve().parents[2] / "data" / "photos" / "cache"
SIZES = (320, 640)
_WIKIMEDIA = re.compile(r"^(https://upload\.wikimedia\.org/wikipedia/commons)/(\w/\w\w)/([^/]+)$")


def download_url(candidate: Candidate) -> str:
    """Wikimedia originals can be huge; ask for a 1280 px rendering instead."""
    match = _WIKIMEDIA.match(candidate.url)
    if match and (candidate.width or 0) > 1280:
        base, folder, name = match.groups()
        return f"{base}/thumb/{folder}/{name}/1280px-{name}"
    return candidate.url


def fetch(candidate: Candidate) -> Path:
    path = CACHE / f"{candidate.id}.img"
    if not path.exists():
        CACHE.mkdir(parents=True, exist_ok=True)
        headers = {"User-Agent": USER_AGENT}
        request = urllib.request.Request(download_url(candidate), headers=headers)
        with urllib.request.urlopen(request, timeout=60) as response:
            path.write_bytes(response.read())
        time.sleep(0.3)
    return path


def crop_box(width: int, height: int, ratio: float = 4 / 3) -> tuple[int, int, int, int]:
    """The largest centred box with this width:height ratio."""
    if width / height > ratio:
        new_width = round(height * ratio)
        left = (width - new_width) // 2
        return left, 0, left + new_width, height
    new_height = round(width / ratio)
    top = (height - new_height) // 2
    return 0, top, width, top + new_height


def _resized(image: Image.Image, width: int) -> Image.Image:
    size = (width, width * 3 // 4)
    # Pillow's stubs leave part of resize's `size` type unknown; the call itself is typed.
    return image.resize(size, Image.Resampling.LANCZOS)  # pyright: ignore[reportUnknownMemberType]


def _cropped(source: Path) -> Image.Image:
    image = Image.open(source).convert("RGB")
    return image.crop(crop_box(*image.size))


def write_webp(source: Path, target: Path) -> list[Path]:
    """`target` without a suffix; writes `<target>-320.webp` and `<target>-640.webp`."""
    image = _cropped(source)
    target.parent.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for width in SIZES:
        path = target.parent / f"{target.name}-{width}.webp"
        _resized(image, width).save(path, "WEBP", quality=72, method=6)
        written.append(path)
    return written


def thumbnail_uri(source: Path, width: int = 200) -> str:
    """A small JPEG as a data URI, for the contact sheet (nothing is hotlinked)."""
    image = _resized(_cropped(source), width)
    buffer = io.BytesIO()
    image.save(buffer, "JPEG", quality=70)
    return "data:image/jpeg;base64," + base64.b64encode(buffer.getvalue()).decode()
