# Problem 2: Answer key (spoilers)

- `recommendations.py`: the reference implementation (copy it over
  `movies/recommendations.py`).
- `views.diff`: the view change (`patch -p1 < SOLUTION/views.diff`).

## Hints (one at a time)

1. `test_requires_authentication` fails because of one line in the view, not
   in the service. Which permission does the project default to?
2. Build two things first: the set of movie ids the user has seen
   (`Rating ∪ WatchedMovie`) and a `dict[genre_id, weight]`.
3. `Movie.objects.annotate(avg_rating=Avg("ratings__score")).filter(avg_rating__gte=7.0)`
   handles both "≥ 7.0" and "no ratings" (NULL fails the filter).
4. Leave watched-and-rated movies out of the watched loop:
   `.exclude(movie_id__in=rated_ids)`.
5. Sort key: `(-score, -avg, title)`. Round only when building the output.

## What each hidden test checks

| Hidden test | Rule | Typical mistake |
|---|---|---|
| `test_returns_at_most_10` | 7 | forgetting the slice, or `count` ≠ `len(results)` |
| `test_response_item_structure_and_rounding` | contract | extra keys, unsorted genres, no rounding |
| `test_unrated_movies_excluded_and_exactly_7_included` | 2 | `> 7` instead of `>= 7`; treating no ratings as 0 or crashing on `None` |
| `test_ties_broken_by_title` | 6 | no tie-break, so order is insertion or id order |
| `test_other_users_history_does_not_exclude` | 1 | `Rating.objects.values("movie")` without `user=` |
| `test_boosts_compound_and_multi_genre_movies_use_mean_weight` | 3, 4 | adding boosts instead of multiplying; max or product instead of mean |
| `test_watched_and_rated_movie_counts_only_as_rated` | 3 | applying both × 1.2 and × 1.1 |
| `test_rating_of_exactly_5_counts_as_disliked` | 3 | `>= 5` instead of `> 5` |
| `test_movie_without_genres_uses_neutral_weight` | 4 | `ZeroDivisionError` on the mean |
| `test_unknown_user_id_returns_401` | contract | regression guard (passes once auth isn't bypassed) |
