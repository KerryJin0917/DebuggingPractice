"""Reference solution for movies/recommendations.py (spoilers).

Copy over movies/recommendations.py and apply SOLUTION/views.diff to check it.
"""
from __future__ import annotations

from collections import defaultdict

from django.db.models import Avg

from .models import Movie, Rating, WatchedMovie

MAX_RESULTS = 10
MIN_AVERAGE_RATING = 7.0
LIKED_THRESHOLD = 5          # score > 5 counts as "liked"
LIKED_MULTIPLIER = 1.2
DISLIKED_MULTIPLIER = 0.8
WATCHED_UNRATED_MULTIPLIER = 1.1


def _genre_weights(user) -> dict[int, float]:
    """Multiplicative weight per genre id, built from the user's history."""
    weights: dict[int, float] = defaultdict(lambda: 1.0)

    ratings = Rating.objects.filter(user=user).select_related("movie").prefetch_related("movie__genres")
    rated_ids = set()
    for rating in ratings:
        rated_ids.add(rating.movie_id)
        factor = LIKED_MULTIPLIER if rating.score > LIKED_THRESHOLD else DISLIKED_MULTIPLIER
        for genre in rating.movie.genres.all():
            weights[genre.id] *= factor

    # A movie that is both watched and rated counts only as rated.
    watched = (
        WatchedMovie.objects.filter(user=user)
        .exclude(movie_id__in=rated_ids)
        .prefetch_related("movie__genres")
    )
    for entry in watched:
        for genre in entry.movie.genres.all():
            weights[genre.id] *= WATCHED_UNRATED_MULTIPLIER

    return weights


def get_recommendations_for_user(user, limit: int = MAX_RESULTS) -> list[dict]:
    weights = _genre_weights(user)

    seen_ids = set(Rating.objects.filter(user=user).values_list("movie_id", flat=True))
    seen_ids |= set(WatchedMovie.objects.filter(user=user).values_list("movie_id", flat=True))

    # avg_rating is NULL for movies nobody rated, so the >= filter drops them too.
    candidates = (
        Movie.objects.exclude(pk__in=seen_ids)
        .annotate(avg_rating=Avg("ratings__score"))
        .filter(avg_rating__gte=MIN_AVERAGE_RATING)
        .prefetch_related("genres")
    )

    scored = []
    for movie in candidates:
        genres = list(movie.genres.all())
        multiplier = sum(weights[g.id] for g in genres) / len(genres) if genres else 1.0
        scored.append((movie.avg_rating * multiplier, movie, genres))

    # Sort on the unrounded values: score desc, average desc, title asc.
    scored.sort(key=lambda item: (-item[0], -item[1].avg_rating, item[1].title))

    return [
        {
            "id": movie.pk,
            "title": movie.title,
            "genres": sorted(g.name for g in genres),
            "average_rating": round(movie.avg_rating, 2),
            "score": round(score, 3),
        }
        for score, movie, genres in scored[:limit]
    ]
