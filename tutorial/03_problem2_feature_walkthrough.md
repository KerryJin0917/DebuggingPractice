# 03: Problem 2 walkthrough (recommendations feature)

> ⚠️ Full spoilers for `problem2_recommendations_feature/`. All commands run
> from that folder. Output is from real runs.

Feature work uses the same loop as debugging. The difference is that the
"bug" is a rule in the spec that isn't implemented yet. The trick is to
**build in stages and run the tests after every stage**, so you're never
more than one rule away from a passing state.

Progress you'll see:

| Stage | What you add | Visible | Hidden |
|---|---|---|---|
| start | nothing (stub returns 501) | 0/6 | 1/10 |
| 1 | wire the view, require auth, service returns `[]` | 1/6 | 1/10 |
| 2 | candidates + quality bar + response shape (no personalization) | 3/6 | 6/10 |
| 3a | genre weights, a "first draft" | **6/6** | 7/10 ← the trap |
| 3b | edge-case audit against the spec | 6/6 | **10/10** |

---

## Phase 0: Turn the spec into a checklist (≈5 min)

Before writing code, rewrite the README's rules as a numbered checklist and
**map each item to a test**. Items with no visible test are where the hidden
tests live.

| # | Rule | Visible test | Edge cases to remember |
|---|---|---|---|
| A | 401 without a valid user | `test_requires_authentication` | unknown user id too |
| B | exclude movies **this user** watched **or** rated | `test_excludes_...` | other users' history must *not* exclude |
| C | average (all users) **≥ 7.0** | `test_only_returns_..._7` | exactly 7.0 is **in**; no ratings is **out** |
| D | rated > 5 → genre × 1.2 | `test_high_rating_...` | weights **multiply** across movies |
| E | rated ≤ 5 → × 0.8 | `test_low_rating_...` | **exactly 5** is a dislike |
| F | watched, unrated → × 1.1 | `test_watched_but_unrated_...` | watched **and** rated → only the rating counts |
| G | multiplier = **mean** of the movie's genre weights | none | no genres → 1.0 (don't divide by zero!) |
| H | score = avg × multiplier | (all scoring tests) | |
| I | sort score ↓, avg ↓, title ↑ | none | tie-breaks |
| J | at most 10 | none | `count` == `len(results)` |
| K | output: `id, title, genres (sorted), average_rating (2dp), score (3dp)` | partly | sort on **unrounded** values |

Run the suite once to see where you're starting:

```
FAIL: test_requires_authentication        AssertionError: 501 != 401
FAIL: test_excludes_movies_user_watched_or_rated
AssertionError: 501 != 200 : b'{"detail":"Not implemented."}'
... (all 6 fail)
```

Interesting: even the auth test fails, and with **501**, not 200. That's a
clue that the view is open to everyone. Look at it.

## Phase 1: Read the code you'll touch

- `movies/views.py`, `RecommendationsView`: `permission_classes = [AllowAny]`
  with a TODO, and it returns 501.
- `movies/recommendations.py`: constants already defined, and a function
  stub that raises `NotImplementedError`.
- `movies/models.py`: `Rating(user, movie, score)`, `WatchedMovie(user, movie)`,
  `Movie.genres` (M2M). The reverse names are `movie.ratings` and
  `movie.watched_by`. You'll need those for ORM lookups like `ratings__score`.
- Settings: `UNAUTHENTICATED_USER: None`, so with `AllowAny` an anonymous
  `request.user` is `None`.

Plan the function as small pieces:

```
seen_ids    = rated_ids ∪ watched_ids                    (B)
weights     = {genre_id: weight} from the user's history (D, E, F)
candidates  = unseen movies annotated with avg, avg ≥ 7  (B, C)
score each  = avg × mean(weights of its genres)          (G, H)
sort, slice, format                                      (I, J, K)
```

---

## Stage 1: wire the view and require auth

`movies/views.py`:

```diff
-from rest_framework.permissions import AllowAny
 ...
 from .models import Movie, Rating, WatchedMovie
+from .recommendations import get_recommendations_for_user
 ...
 class RecommendationsView(APIView):
-    permission_classes = [AllowAny]  # TODO: lock down before release
-
     def get(self, request):
-        return Response({"detail": "Not implemented."}, status=status.HTTP_501_NOT_IMPLEMENTED)
+        results = get_recommendations_for_user(request.user)
+        return Response({"count": len(results), "results": results})
```

Removing `AllowAny` falls back to the project default (`IsAuthenticated` in
`settings.py`). The auth class already defines `authenticate_header`, so you
get 401, not 403.

`movies/recommendations.py`, a temporary body so the endpoint returns 200:

```python
def get_recommendations_for_user(user, limit: int = MAX_RESULTS) -> list[dict]:
    return []
```

```
FAIL: test_excludes_movies_user_watched_or_rated
FAIL: test_high_rating_boosts_similar_genres
FAIL: test_low_rating_favors_other_genres
FAIL: test_only_returns_movies_with_average_rating_of_at_least_7
FAIL: test_watched_but_unrated_movie_boosts_similar_genres
Ran 6 tests
```

**1/6.** Auth works and the plumbing is proven. Each failure is now about
logic, not wiring.

## Stage 2: candidates, quality bar, response shape

Add the rules that don't need personalization (B, C, K), with score = average
for now:

```python
from django.db.models import Avg

from .models import Movie, Rating, WatchedMovie


def _seen_movie_ids(user) -> set[int]:
    rated = Rating.objects.filter(user=user).values_list("movie_id", flat=True)
    watched = WatchedMovie.objects.filter(user=user).values_list("movie_id", flat=True)
    return set(rated) | set(watched)


def get_recommendations_for_user(user, limit: int = MAX_RESULTS) -> list[dict]:
    candidates = (
        Movie.objects.exclude(pk__in=_seen_movie_ids(user))
        .annotate(avg_rating=Avg("ratings__score"))
        .filter(avg_rating__gte=MIN_AVERAGE_RATING)
        .prefetch_related("genres")
    )
    results = []
    for movie in candidates:
        score = movie.avg_rating  # no personalization yet
        results.append({
            "id": movie.pk,
            "title": movie.title,
            "genres": sorted(g.name for g in movie.genres.all()),
            "average_rating": round(movie.avg_rating, 2),
            "score": round(score, 3),
        })
    results.sort(key=lambda r: -r["score"])
    return results[:limit]
```

Why this works:
- `annotate(avg_rating=Avg("ratings__score"))` computes the average over
  **all users'** ratings in SQL.
- A movie with no ratings gets `avg_rating = NULL`, and `NULL >= 7.0` is
  false in SQL, so rule C's "no ratings → excluded" comes free.
- `__gte` (not `__gt`) gives "exactly 7.0 is in".

```
FAIL: test_high_rating_boosts_similar_genres
FAIL: test_low_rating_favors_other_genres
FAIL: test_watched_but_unrated_movie_boosts_similar_genres
Ran 6 tests
```

**3/6.** The remaining failures are exactly the three personalization rules.
That's the signal that stage 2 is correct and complete.

## Stage 3a: genre weights (the "first draft")

Here's a typical first attempt. It looks reasonable, and it **passes all 6
visible tests**:

```python
def get_recommendations_for_user(user, limit: int = MAX_RESULTS) -> list[dict]:
    weights = {}
    for rating in Rating.objects.filter(user=user):
        factor = 1.2 if rating.score > 5 else 0.8
        for genre in rating.movie.genres.all():
            weights[genre.id] = weights.get(genre.id, 1.0) * factor
    for watched in WatchedMovie.objects.filter(user=user):
        for genre in watched.movie.genres.all():
            weights[genre.id] = weights.get(genre.id, 1.0) * 1.1

    # ... same seen_ids / candidates query as stage 2 ...
    for movie in candidates:
        genres = list(movie.genres.all())
        multiplier = sum(weights.get(g.id, 1.0) for g in genres) / len(genres)
        score = movie.avg_rating * multiplier
        ...
    results.sort(key=lambda r: -r["score"])
    return results[:limit]
```

```
Ran 6 tests
OK
```

It's tempting to stop here. **Don't.** The hidden tests on this draft:

```
ERROR: test_movie_without_genres_uses_neutral_weight
ZeroDivisionError: division by zero
FAIL: test_ties_broken_by_title
AssertionError: Lists differ: ['Zodiac', 'Alien', 'Memento'] != ['Alien', 'Memento', 'Zodiac']
FAIL: test_watched_and_rated_movie_counts_only_as_rated
AssertionError: 9.9 != 9.0 within 3 places
Ran 10 tests
FAILED (failures=2, errors=1)
```

**7/10.** Each of these failures is a checklist item with **no visible
test**: G (no genres), I (tie-break), and F's edge case (watched and rated).
That's why you build the checklist in Phase 0.

## Stage 3b: audit the draft against the checklist

Walk through the checklist line by line and ask "what does my code do in the
edge case?" Writing a probe test for each is fastest, as in walkthrough 02.

| Item | Draft behavior | Fix |
|---|---|---|
| F: watched **and** rated | movie is in both loops, so × 1.2 × 1.1 = 1.32 | skip rated movies in the watched loop: `.exclude(movie_id__in=rated_ids)` |
| G: no genres | `/ len([])` raises `ZeroDivisionError` | `... if genres else 1.0` |
| I: tie-break | sorts by score only, so ties come out in DB order | key `(-score, -avg, title)` |
| K: sort on unrounded | draft sorts on the rounded dict values | sort tuples of raw values, format last |
| E: exactly 5 | `> 5` is a like, so 5 is a dislike ✓ | none |
| D: compounding | `*=` ✓ | none |

Final version (`SOLUTION/recommendations.py`), showing only the parts that
changed:

```python
def _genre_weights(user) -> dict[int, float]:
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

# in get_recommendations_for_user:
    scored = []
    for movie in candidates:
        genres = list(movie.genres.all())
        multiplier = sum(weights[g.id] for g in genres) / len(genres) if genres else 1.0
        scored.append((movie.avg_rating * multiplier, movie, genres))

    scored.sort(key=lambda item: (-item[0], -item[1].avg_rating, item[1].title))
    return [ {...format, rounding here...} for score, movie, genres in scored[:limit] ]
```

```bash
python manage.py test tests hidden_tests
```
```
Ran 16 tests
OK
```

Also use the named constants (`LIKED_MULTIPLIER`, `MIN_AVERAGE_RATING`, …)
that were already in the stub instead of magic numbers. Reviewers notice.

---

## Stretch: query count

The draft runs queries **inside loops** (`rating.movie`, then
`movie.genres.all()` per movie), the classic N+1 problem. Measured with
`CaptureQueriesContext`:

| Implementation | 5 movies | 55 movies |
|---|---|---|
| first draft | 14 queries | 98 queries |
| final (`select_related` + `prefetch_related` + `annotate`) | 9 queries | 9 queries |

To lock it in with a test:

```python
with self.assertNumQueries(9):
    self.client.get(URL, HTTP_X_USER_ID=str(alice.pk))
```

(The exact number depends on your implementation. What matters is that it
**doesn't grow** with the number of movies.)

---

## What to take away

1. **Spec → checklist → test map** before coding. Unmapped rules are where
   the hidden tests are.
2. **Stage the build** so each stage turns a known set of tests green. If a
   stage turns the "wrong" tests green or red, you know right away which
   rule is off.
3. **Wire first.** A trivial `return []` behind the real view proves the
   URL, auth, and response shape before any logic.
4. **Let the database do the work.** `annotate(Avg(...))` plus a filter
   handles averages, thresholds, and NULLs in one query.
5. **6/6 isn't done.** Audit every checklist item for its edge case:
   boundaries (`>=`, exactly 5), empty collections (divide by zero),
   overlaps (watched *and* rated), and tie-breaks.
6. **Compute with raw values, round only for output.**
