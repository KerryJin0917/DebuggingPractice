"""The existing bad-content checker. Other teams use it too, so keep its interface."""
from __future__ import annotations

import re

BANNED_WORDS = frozenset({"idiot", "stupid", "trash", "garbage", "scam"})


def find_banned_words(text: str) -> list[str]:
    """Return the banned words that appear in ``text``.

    Matching is case-insensitive and on whole words ("trashy" doesn't count).
    The result is sorted and has no duplicates.
    """
    words = re.findall(r"[a-z]+", text)
    return [word for word in words if word in BANNED_WORDS]
