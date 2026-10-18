"""The photo pipeline's pure parts: ranking, cropping, credits and picks. No network."""

from typing import Any

import pytest

from scripts.photos.credits import credit_line
from scripts.photos.images import crop_box, download_url
from scripts.photos.import_photos import chosen, with_photo
from scripts.photos.openverse import Candidate
from scripts.photos.rank import best, simpler, slug, words


def photo(id: str, title: str, width: int = 1024, height: int = 768, **extra: Any) -> Candidate:
    base: dict[str, Any] = {
        "id": id,
        "title": title,
        "url": f"https://example.org/{id}.jpg",
        "foreign_landing_url": f"https://example.org/{id}",
        "license": "by",
        "license_version": "2.0",
        "width": width,
        "height": height,
    }
    return Candidate.model_validate(base | extra)


def test_slugs_and_words() -> None:
    assert slug("Mapo Tofu (Sichuan)") == "mapo-tofu-sichuan"
    assert words("Classic Smash and Fries") == {"smash", "fries", "frie"}


def test_simpler_searches_drop_words_and_try_endings_first() -> None:
    assert simpler("Classic Smash Burger")[:2] == ["Smash Burger", "Burger"]
    assert simpler("Whole Sea Bream")[0] == "Sea Bream"
    assert simpler("Sayadiyah") == []


def test_the_best_photo_names_the_dish_and_is_big_enough() -> None:
    noodle = photo("a", "Bowl of noodles")
    tofu = photo("b", "Mapo tofu in Chengdu")
    tagged = photo("c", "Dinner", tags=["mapo tofu"])
    tiny = photo("d", "Mapo tofu", width=300, height=200)
    assert [c.id for c in best([noodle, tagged, tiny, tofu], "Mapo Tofu")] == ["b", "c", "a"]


def test_crop_box_is_centred_four_by_three() -> None:
    assert crop_box(1600, 900) == (200, 0, 1400, 900)
    assert crop_box(900, 1200) == (0, 262, 900, 937)
    assert crop_box(800, 600) == (0, 0, 800, 600)


def test_large_wikimedia_originals_download_as_a_1280_rendering() -> None:
    url = "https://upload.wikimedia.org/wikipedia/commons/1/18/Shakshuka.jpg"
    big = photo("w", "Shakshuka", width=3984, height=2988, url=url)
    assert download_url(big).endswith("/thumb/1/18/Shakshuka.jpg/1280px-Shakshuka.jpg")
    assert download_url(photo("f", "x")) == "https://example.org/f.jpg"


def test_a_credit_names_title_creator_licence_and_source() -> None:
    candidate = photo("a", "Mapo tofu", creator="Jo", license_url="https://cc.org/by/2.0/")
    line = credit_line("Golden Dragon, Mapo Tofu", "golden-dragon/mapo-tofu", candidate)
    assert line == (
        '- **Golden Dragon, Mapo Tofu** (`golden-dragon/mapo-tofu`): "Mapo tofu" by Jo, '
        "[CC BY 2.0](https://cc.org/by/2.0/), [source](https://example.org/a)."
    )


def test_picks_choose_an_alternate_or_none_and_default_to_the_first() -> None:
    found = {"r/d": {"candidates": [photo("a", "x").model_dump(), photo("b", "y").model_dump()]}}
    assert (got := chosen("r/d", found, {})) is not None and got.id == "a"
    assert (got := chosen("r/d", found, {"r/d": "B"})) is not None and got.id == "b"
    assert chosen("r/d", found, {"r/d": "none"}) is None
    assert chosen("r/d", found, {"r/d": "C"}) is None
    assert chosen("r/missing", found, {}) is None


def test_the_photo_field_goes_after_the_name_or_away() -> None:
    record = {"name": "Latte", "category": "coffee", "photo": "old/one"}
    assert list(with_photo(record, "cafe/latte")) == ["name", "photo", "category"]
    assert with_photo(record, "cafe/latte")["photo"] == "cafe/latte"
    assert "photo" not in with_photo(record, None)


def test_a_licence_outside_adr_0024_is_refused() -> None:
    found = {"r/d": {"candidates": [photo("a", "x", license="by-nc").model_dump()]}}
    with pytest.raises(ValueError, match="not allowed"):
        chosen("r/d", found, {})
