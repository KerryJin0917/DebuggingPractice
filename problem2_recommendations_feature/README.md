# Problem 2: "Recommended For You" (feature implementation only)

**Time limit: 60 minutes.** Nothing here is broken. The feature just doesn't
exist yet.

**MovieNight** lets users mark movies as watched and rate them 1–10. The
frontend has a **Recommended For You** carousel that calls
`GET /api/ratings/recommendations/user`, but that endpoint is a stub that
returns `501`, so the carousel is always empty. Build it.

## What to build

1. `movies/recommendations.py`: implement `get_recommendations_for_user(user, limit=10)`.
2. `movies/views.py`: wire `RecommendationsView` to it and make it
   **require authentication** (the scaffolding left it open).

Nothing else should need to change. Everything in `models.py`,
`serializers.py`, the other views, and the auth class already works.

## Rules

- Don't change `tests/`. The 6 tests in `tests/test_recommendations.py` are
  the acceptance contract.
- Don't open `hidden_tests/` or `SOLUTION/` until you're done. The hidden
  tests check the edge cases in the rules below, so implement the rules, not
  just the visible tests.
- AI use (to match the OA): your assistant may only see **one file at a
  time**, the one you have open. Give it the relevant rule and model fields
  yourself.

## Setup

```bash
pip install -r ../requirements.txt
python manage.py test tests            # 6 acceptance tests (all fail at first)
```

To try it by hand:

```bash
python manage.py migrate
python manage.py seed_demo             # alice + critics + 15 rated movies
python manage.py runserver
curl -s -X POST -H "X-User-Id: 1" localhost:8000/api/movies/2/watched/
curl -s -X POST -H "X-User-Id: 1" -H "Content-Type: application/json" -d '{"movie_id": 3, "score": 9}' localhost:8000/api/ratings/
curl -s -H "X-User-Id: 1" localhost:8000/api/ratings/recommendations/user
```

## Models you'll use

```
Genre(name)
Movie(title, release_year, genres: M2M Genre)    movie.ratings, movie.watched_by
Rating(user, movie, score 1-10)                  unique per (user, movie)
WatchedMovie(user, movie)                        unique per (user, movie)
```

Existing endpoints (already working): `GET /api/movies/`,
`POST /api/movies/<id>/watched/`, `POST /api/ratings/` `{"movie_id", "score"}`.

## API contract

`GET /api/ratings/recommendations/user` with header `X-User-Id: <id>`

- Missing header, or an unknown user: **401**.
- Success: **200**

```json
{
  "count": 2,
  "results": [
    {"id": 7, "title": "Arrival", "genres": ["Drama", "Sci-Fi"], "average_rating": 7.5, "score": 9.0},
    {"id": 3, "title": "Heat", "genres": ["Action", "Crime"], "average_rating": 8.0, "score": 8.0}
  ]
}
```

`genres` are sorted by name. `average_rating` is rounded to 2 decimals and
`score` to 3. Rounding is for display only: sort on the unrounded values.

## Recommendation rules

1. **Candidates**: every movie the user has **not** watched and **not**
   rated. Other users' history doesn't matter.
2. **Quality bar**: a candidate's average rating (across **all** users'
   ratings) must be **≥ 7.0**. A movie with no ratings has no average and is
   never recommended.
3. **Genre weights**: every genre starts at weight `1.0`. Walk through the
   user's history and multiply the weight of **each genre** of each movie:
   - rated **above 5** (6–10): × **1.2** (boost similar genres)
   - rated **5 or below**: × **0.8** (favor other genres)
   - watched but **not rated**: × **1.1** (mild boost)
   - watched **and** rated: counts as **rated only**, not both

   Multipliers stack: two liked Sci-Fi movies give Sci-Fi `1.2 × 1.2 = 1.44`.
4. **Movie multiplier**: the **mean** of the weights of the candidate's
   genres, or `1.0` if it has no genres.
5. **Score** = `average_rating × movie multiplier`.
6. **Order**: score descending, then average rating descending, then title
   ascending.
7. Return at most **10**.

### Worked example

Alice rated *Interstellar* (Sci-Fi) a 9, so Sci-Fi is weighted 1.2.

| Candidate | Genres | Avg | Multiplier | Score |
|---|---|---|---|---|
| Arrival | Sci-Fi | 7.5 | 1.2 | **9.0** |
| Dune | Sci-Fi, Drama | 8.0 | (1.2 + 1.0) / 2 = 1.1 | **8.8** |
| Heat | Crime | 8.0 | 1.0 | **8.0** |
| Cats | Musical | 4.0 | n/a | excluded (avg < 7) |

Result order: Arrival, Dune, Heat.

## Scoring yourself

| Stage | Command | Target |
|---|---|---|
| Acceptance | `python manage.py test tests` | 6/6 |
| Hidden | `python manage.py test hidden_tests` | 10/10 |

Stretch goal (not graded): keep it to a fixed number of queries no matter how
many movies there are. Use `annotate(Avg(...))` and `prefetch_related` instead
of querying per movie, and check with `assertNumQueries`.
