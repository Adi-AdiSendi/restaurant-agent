"""Turn the storefront signs (3:1, supplied by the project owner) into WebP banners.

Usage: uv run python -m scripts.photos.storefronts <folder of signs>

Each file is matched to the restaurant whose name it starts with, e.g.
"Golden Dragon Chinese Restaurant Sign.png". The sign keeps its 3:1 shape, so the
lettering is never cropped; the UI loads `/storefronts/<slug>-{720,1440}.webp`.
"""

import sys
from pathlib import Path

from PIL import Image

from scripts.seed_menu import load_restaurants

OUT = Path(__file__).resolve().parents[3] / "frontend" / "public" / "storefronts"
WIDTHS = (720, 1440)


def match(names: list[str], file_name: str) -> str | None:
    """The restaurant name the file starts with (case-insensitive), longest first."""
    lowered = file_name.lower()
    hits = [n for n in names if lowered.startswith(n.lower())]
    return max(hits, key=len) if hits else None


def main(folder: Path) -> None:
    slugs = {r.name: r.slug for r in load_restaurants()}
    OUT.mkdir(parents=True, exist_ok=True)
    for path in sorted(folder.iterdir()):
        name = match(list(slugs), path.name)
        if name is None:
            print(f"skipped {path.name}: no restaurant name at its start")
            continue
        image = Image.open(path).convert("RGB")
        for width in WIDTHS:
            size = (width, width // 3)
            # Pillow's stubs leave part of resize's `size` type unknown; the call is typed.
            banner = image.resize(size, Image.Resampling.LANCZOS)  # pyright: ignore[reportUnknownMemberType]
            banner.save(OUT / f"{slugs[name]}-{width}.webp", "WEBP", quality=78, method=6)
        print(f"{slugs[name]}: {path.name}")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
