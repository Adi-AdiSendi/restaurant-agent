"""Turn the reviewed picks into WebP files, `photo` fields and credits (ADR 0024).

Usage: uv run python -m scripts.photos.import_photos

data/photos/picks.json holds the user's changes to the contact sheet, by key:
"B" or "C" for an alternate, "none" for the icon. Anything not listed keeps
the script's pick ("A"). Reruns are safe: files are rewritten and files no
longer picked are deleted.
"""

import json
from pathlib import Path
from typing import Any

from scripts.photos.credits import HEADER, credit_line
from scripts.photos.find_candidates import CANDIDATES
from scripts.photos.images import fetch, write_webp
from scripts.photos.openverse import LICENCES, Candidate
from scripts.photos.rank import slug

BACKEND = Path(__file__).resolve().parents[2]
RESTAURANTS = BACKEND / "data" / "restaurants"
PICKS = BACKEND / "data" / "photos" / "picks.json"
PUBLIC = BACKEND.parent / "frontend" / "public" / "menu"
CREDITS = BACKEND.parent / "docs" / "photo-credits.md"


def chosen(key: str, found: dict[str, Any], picks: dict[str, str]) -> Candidate | None:
    options = [Candidate.model_validate(c) for c in found.get(key, {}).get("candidates", [])]
    letter = picks.get(key, "A")
    index = "ABC".find(letter)
    candidate = options[index] if letter != "none" and 0 <= index < len(options) else None
    if candidate and candidate.license not in LICENCES.split(","):
        raise ValueError(f"{key}: licence {candidate.license!r} is not allowed (ADR 0024)")
    return candidate


def with_photo(record: dict[str, Any], photo: str | None) -> dict[str, Any]:
    """The record with `photo` right after `name`, or without it."""
    rebuilt: dict[str, Any] = {}
    for field, value in record.items():
        if field != "photo":
            rebuilt[field] = value
        if field == "name" and photo:
            rebuilt["photo"] = photo
    return rebuilt


def main() -> None:
    found = json.loads(CANDIDATES.read_text(encoding="utf-8"))
    picks: dict[str, str] = json.loads(PICKS.read_text(encoding="utf-8")) if PICKS.exists() else {}
    credits: list[str] = []
    written: set[Path] = set()
    # Data and credits are written only after every photo downloaded and converted,
    # so a failed download leaves the menu files and credits as they were.
    texts: dict[Path, str] = {}
    for path in sorted(RESTAURANTS.glob("*.json")):
        data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
        rslug = data["slug"]
        records = [(data, "cover", data["name"])] + [
            (item, slug(item["name"]), f"{data['name']}, {item['name']}") for item in data["items"]
        ]
        for record, name, label in records:
            candidate = chosen(f"{rslug}/{name}", found, picks)
            photo = f"{rslug}/{name}" if candidate else None
            if candidate and photo:
                written.update(write_webp(fetch(candidate), PUBLIC / rslug / name))
                credits.append(credit_line(label, photo, candidate))
            updated = with_photo(record, photo)
            record.clear()
            record.update(updated)
        texts[path] = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    for path, text in texts.items():
        path.write_text(text, encoding="utf-8", newline="\n")
    for stale in set(PUBLIC.rglob("*.webp")) - written:
        stale.unlink()
    CREDITS.write_text(HEADER + "\n".join(credits) + "\n", encoding="utf-8", newline="\n")
    print(f"{len(credits)} photos written; credits in {CREDITS}")


if __name__ == "__main__":
    main()
