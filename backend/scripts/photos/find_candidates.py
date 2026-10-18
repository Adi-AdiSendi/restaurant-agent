"""Find the best few Openverse photos for every dish and restaurant cover (ADR 0024).

Usage: uv run python -m scripts.photos.find_candidates [--retry-thin]

Results are cached in data/photos/candidates.json, so a rerun only searches what
is missing. The anonymous quota is 20 searches a minute and 200 a day; on a 429
the script saves and stops, and a later run carries on.
"""

import json
import sys
import time
from pathlib import Path
from typing import cast

from scripts.photos.openverse import Candidate, RateLimited, search
from scripts.photos.rank import best, simpler, slug, usable
from scripts.seed_menu import load_restaurants

CANDIDATES = Path(__file__).resolve().parents[2] / "data" / "photos" / "candidates.json"
QUERIES = CANDIDATES.parent / "queries.json"
"""Hand-written searches by key, for dishes whose name finds nothing (e.g. "Sayadiyah")."""
PAUSE_S = 3.5
"""About 17 searches a minute, under the burst limit of 20."""


def targets() -> list[tuple[str, str, list[str]]]:
    """(key, name to rank against, queries to try in order) for every photo needed."""
    found: list[tuple[str, str, list[str]]] = []
    for restaurant in load_restaurants():
        cuisine = restaurant.cuisine.lower()
        cover = f"{cuisine} food"
        found.append((f"{restaurant.slug}/cover", cover, [cover, f"{cuisine} restaurant"]))
        for item in restaurant.items:
            queries = [item.name, *simpler(item.name)][:4]
            found.append((f"{restaurant.slug}/{slug(item.name)}", item.name, queries))
    return found


def load() -> dict[str, dict[str, object]]:
    return json.loads(CANDIDATES.read_text(encoding="utf-8")) if CANDIDATES.exists() else {}


def save(cache: dict[str, dict[str, object]]) -> None:
    CANDIDATES.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(cache, indent=2, ensure_ascii=False, sort_keys=True)
    CANDIDATES.write_text(text + "\n", encoding="utf-8", newline="\n")


def _thin(entry: dict[str, object] | None) -> list[Candidate]:
    found = cast(list[object], entry.get("candidates", [])) if entry else []
    return [Candidate.model_validate(c) for c in found]


def main(retry_thin: bool = False) -> None:
    """`retry_thin`: search again, with other queries, where fewer than 2 were found."""
    cache = load()
    overrides: dict[str, list[str]] = (
        json.loads(QUERIES.read_text(encoding="utf-8")) if QUERIES.exists() else {}
    )
    try:
        for key, name, queries in targets():
            pool = _thin(cache.get(key))
            if key in cache and not (retry_thin and len(pool) < 2):
                continue
            tries = overrides.get(key) or (queries[1:] if key in cache else queries)
            used = ""
            for query in tries:
                time.sleep(PAUSE_S)
                pool += search(query)
                used = query
                if sum(usable(c) for c in pool) >= 3:
                    break
            picks = best(pool, name)
            cache[key] = {"query": used, "candidates": [c.model_dump() for c in picks]}
            print(f"{len(picks)} {key} ({used!r})", flush=True)
            save(cache)
    except RateLimited:
        print("Openverse quota used up; run again later to carry on.")
    print(f"{len(cache)} of {len(targets())} targets have results in {CANDIDATES}")


if __name__ == "__main__":
    main(retry_thin="--retry-thin" in sys.argv)
