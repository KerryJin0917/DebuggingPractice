"""Personalized movie recommendations.

TODO(you): implement ``get_recommendations_for_user``. The full spec is in the
README ("Recommendation rules"). The bundled tests are the acceptance contract.
"""
from __future__ import annotations

from .models import Movie, Rating, WatchedMovie  # noqa: F401 (you'll need these)

MAX_RESULTS = 10
MIN_AVERAGE_RATING = 7.0
LIKED_THRESHOLD = 5          # score > 5 counts as "liked"
LIKED_MULTIPLIER = 1.2
DISLIKED_MULTIPLIER = 0.8
WATCHED_UNRATED_MULTIPLIER = 1.1


def get_recommendations_for_user(user, limit: int = MAX_RESULTS) -> list[dict]:
    """Return up to ``limit`` recommendation dicts for ``user``, best first.

    Each dict has: ``id``, ``title``, ``genres`` (sorted list of names),
    ``average_rating`` (rounded to 2 places) and ``score`` (rounded to 3).
    """
    raise NotImplementedError
