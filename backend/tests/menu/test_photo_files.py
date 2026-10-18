"""Every named photo has its files and a credit, and every file is named and credited."""

import re
from pathlib import Path

from scripts.seed_menu import load_restaurants

REPO = Path(__file__).resolve().parents[3]
PUBLIC = REPO / "frontend" / "public" / "menu"
CREDITS = REPO / "docs" / "photo-credits.md"


def named_photos() -> set[str]:
    photos: set[str] = set()
    for restaurant in load_restaurants():
        if restaurant.photo:
            photos.add(restaurant.photo)
        photos |= {item.photo for item in restaurant.items if item.photo}
    return photos


def test_every_named_photo_has_both_sizes() -> None:
    missing = [
        f"{photo}-{size}.webp"
        for photo in sorted(named_photos())
        for size in (320, 640)
        if not (PUBLIC / f"{photo}-{size}.webp").is_file()
    ]
    assert not missing


def test_every_file_is_named_by_a_dish_or_restaurant() -> None:
    files: set[str] = (
        {p.relative_to(PUBLIC).as_posix() for p in PUBLIC.rglob("*.webp")}
        if PUBLIC.exists()
        else set[str]()
    )
    odd = sorted(f for f in files if not re.fullmatch(r".+-(320|640)\.webp", f))
    assert not odd
    unnamed = {f.rsplit("-", 1)[0] for f in files} - named_photos()
    assert not unnamed


def test_every_named_photo_is_credited_once() -> None:
    text = CREDITS.read_text(encoding="utf-8") if CREDITS.exists() else ""
    uncredited = [p for p in sorted(named_photos()) if text.count(f"(`{p}`)") != 1]
    assert not uncredited
