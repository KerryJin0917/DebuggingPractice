# Problem 1: Movie Watch-List API (debugging only)

**Time limit: 60 minutes.** No new features are needed. Everything is already
written and something in it is broken.

You're on call for **CineList**, a small Django REST Framework service that
lets users keep watch lists of movies. QA filed the bug report below. Reproduce
each issue, find the module that causes it, fix it, and get the test suite green.

## Bug report from QA

1. **Adding a movie to a watch list doesn't stick.** The API answers
   `201 Created`, but the movie never shows up in the list afterward.
2. **Adding a movie to a watch list that doesn't exist crashes the server**
   (500) instead of returning `404 {"detail": "Watch list not found."}`.
3. **Removing a movie from a watch list does nothing.** The API answers
   `204`, but the movie is still there.

> Like the real OA, this list isn't complete. The 6 acceptance tests and the
> hidden grader tests also cover behavior QA didn't report. Read the API
> contract below carefully: it's the source of truth.

## Rules

- Don't change the **assertions** in `tests/test_watchlists.py`. Test
  *helpers* can be broken too, and fixing those is allowed.
- Don't open `hidden_tests/` or `SOLUTION/` until you're done.
- AI use (to match the OA): your assistant may only see **one file at a
  time**. Paste in a failing test or a traceback and ask it to narrow the bug
  down to a file, then a function, then a line range. Don't ask for whole-file
  rewrites.

## Setup

```bash
pip install -r ../requirements.txt
python manage.py test tests            # the 6 acceptance tests
```

To try it by hand:

```bash
python manage.py migrate
python manage.py seed_demo             # prints user ids and movie ids
python manage.py runserver
curl -s -H "X-User-Id: 1" localhost:8000/api/watchlists/
```

## Project layout

```
watchlist_project/     settings + root urls
movies/
  authentication.py    X-User-Id header auth
  models.py            Movie, WatchList, WatchListEntry (through table)
  serializers.py       request validation and response shapes
  services.py          business logic (views call into this)
  views.py             DRF APIViews
  urls.py              routes
tests/
  factories.py         test helpers
  test_watchlists.py   the 6 acceptance tests
hidden_tests/          grader's extra tests (spoilers)
SOLUTION/              answer key (spoilers)
```

## API contract

Every endpoint needs the header `X-User-Id: <user id>`.

- Missing header: **401**.
- Unknown user id: **401** `{"detail": "Invalid X-User-Id header."}`.
- A watch list that doesn't exist **or belongs to someone else**: **404**
  `{"detail": "Watch list not found."}`. Other users' lists must never be
  visible or editable.

A watch list is returned as:

```json
{
  "id": 1,
  "name": "Weekend",
  "description": "",
  "movies": [{"id": 2, "title": "Arrival", "genre": "Sci-Fi", "release_year": 2016}],
  "movie_count": 1,
  "created_at": "...",
  "updated_at": "..."
}
```

| Method | Path | Body | Success | Errors |
|---|---|---|---|---|
| GET | `/api/movies/` | | 200, list of movies | |
| GET | `/api/watchlists/` | | 200, the caller's lists, newest first | |
| POST | `/api/watchlists/` | `{"name", "description"?}` | **201**, the new list | 400 if `name` is missing or blank |
| GET | `/api/watchlists/<id>/` | | 200 | 404 |
| PATCH | `/api/watchlists/<id>/` | any of `name`, `description` | 200, changes saved to the DB | 400, 404 |
| DELETE | `/api/watchlists/<id>/` | | **204**, empty body | 404 |
| POST | `/api/watchlists/<id>/movies/` | `{"movie_id"}` | **201**, the updated list | 404 list not found; 404 `"Movie not found."`; **409** `"Movie is already in this watch list."` |
| DELETE | `/api/watchlists/<id>/movies/<movie_id>/` | | **204** | 404 list not found; 404 `"Movie is not in this watch list."` |
| POST | `/api/watchlists/<id>/movies/bulk/` | `{"add": [ids]?, "remove": [ids]?}` | 200, the updated list | 404 |

**Bulk rules:** every id in `add` is applied, then every id in `remove`.
Movies already in the list are skipped on add, and movies not in the list are
skipped on remove. If any id in `add` is an unknown movie, the request returns
404 and **nothing** changes.

## Scoring yourself

| Stage | Command | Target |
|---|---|---|
| Acceptance | `python manage.py test tests` | 6/6 |
| Hidden | `python manage.py test hidden_tests` | 7/7 |

Hints, in increasing spoiler order, are at the top of `SOLUTION/SOLUTION.md`.
