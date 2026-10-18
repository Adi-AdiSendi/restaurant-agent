"""Search Openverse for openly licensed photos (ADR 0024). No key: 20/min, 200/day."""

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import cast

from pydantic import BaseModel

API = "https://api.openverse.org/v1/images/"
USER_AGENT = "restaurant-agent-photo-script/0.1 (prototype menu photos)"
LICENCES = "cc0,pdm,by,by-sa"
"""Only licences that allow changes and commercial use."""


class RateLimited(Exception):
    """The anonymous quota is used up; run again later, the cache keeps what was found."""


class Candidate(BaseModel):
    id: str
    title: str
    url: str
    foreign_landing_url: str
    creator: str | None = None
    creator_url: str | None = None
    license: str
    license_version: str | None = None
    license_url: str | None = None
    width: int | None = None
    height: int | None = None
    tags: list[str] = []


def _tag_names(tags: object) -> list[str]:
    if not isinstance(tags, list):
        return []
    names: list[str] = []
    for tag in cast(list[object], tags):
        if isinstance(tag, dict):
            names.append(str(cast(dict[str, object], tag).get("name", "")))
    return names


def _candidate(raw: dict[str, object]) -> Candidate:
    tags = _tag_names(raw.get("tags"))
    return Candidate.model_validate({**raw, "title": raw.get("title") or "", "tags": tags})


def search(query: str, page_size: int = 20) -> list[Candidate]:
    params = urllib.parse.urlencode(
        {
            "q": query,
            "license": LICENCES,
            "category": "photograph",
            "page_size": page_size,
            "mature": "false",
        }
    )
    request = urllib.request.Request(f"{API}?{params}", headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = json.loads(response.read())
    except urllib.error.HTTPError as exc:
        if exc.code == 429:
            raise RateLimited(query) from exc
        raise
    return [_candidate(raw) for raw in body.get("results", [])]
