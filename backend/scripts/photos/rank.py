"""Rank photo candidates for a dish. Pure functions, so they are tested without a network."""

import re

from scripts.photos.openverse import Candidate

MIN_WIDTH, MIN_HEIGHT = 640, 480
_WORD = re.compile(r"[a-z]+")
_STOP = {"and", "with", "the", "of", "a", "in", "on", "our", "house", "classic", "special"}


def words(text: str) -> set[str]:
    """Lowercase words without stop words, each also without a plural "s"."""
    found = {w for w in _WORD.findall(text.lower()) if w not in _STOP and len(w) > 1}
    return found | {w[:-1] for w in found if w.endswith("s") and len(w) > 3}


def simpler(name: str) -> list[str]:
    """Shorter searches for a dish name, longest first: Openverse matches every word,
    so "Classic Smash Burger" finds nothing where "Smash Burger" does."""
    parts = [w for w in re.findall(r"[A-Za-z]+", name) if w.lower() not in _STOP]
    found: list[str] = []
    for size in range(len(parts), 0, -1):
        # Endings first: the dish noun usually comes last ("Sea Bream", "Noodle Bowl").
        for start in reversed(range(len(parts) - size + 1)):
            phrase = " ".join(parts[start : start + size])
            if phrase not in found and phrase.lower() != name.lower():
                found.append(phrase)
    return found


def slug(text: str) -> str:
    return "-".join(_WORD.findall(text.lower()))


def usable(candidate: Candidate) -> bool:
    width, height = candidate.width or 0, candidate.height or 0
    return width >= MIN_WIDTH and height >= MIN_HEIGHT


def score(candidate: Candidate, name: str) -> float:
    """Words of the dish name found in the title (most) or tags, then a landscape bonus."""
    wanted = words(name)
    in_title = len(wanted & words(candidate.title))
    in_tags = len(wanted & words(" ".join(candidate.tags)))
    width, height = candidate.width or 1, candidate.height or 1
    landscape = 0.5 if 1.2 <= width / height <= 1.8 else 0.0
    return (2 * in_title + in_tags) / max(len(wanted), 1) + landscape


def best(candidates: list[Candidate], name: str, keep: int = 3) -> list[Candidate]:
    """The usable candidates, best first; ties keep Openverse's own order."""
    ranked = sorted(
        (c for c in candidates if usable(c)), key=lambda c: score(c, name), reverse=True
    )
    return ranked[:keep]
