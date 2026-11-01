# Problem 3: Movie Reviews & Moderation (debugging only)

**Time limit: 60 minutes.** No new features are needed. Everything is
written, and some of it is wrong.

**ReelTalk** lets users search movies and post reviews. Reviews go through an
existing bad-content checker, and users who keep posting abusive reviews get
flagged and blocked. Support passed along the complaints below. Reproduce
them, find the cause, fix it, and get the tests green.

> New to the loop? Follow **Part A** of
> [`../tutorial/05_debugging_loop_step_by_step.md`](../tutorial/05_debugging_loop_step_by_step.md)
> while you work. Part B of that file solves this problem, so skip it until
> you're done.

## Support tickets

1. **"Searching for a movie returns the entire catalogue."**
2. **"I can't post a review. I just get a 400 error."** (The user's review was clean.)
3. **"Users who post abusive reviews never get flagged, however many times they do it."**

> As in the OA, this list isn't complete. The 6 acceptance tests and the
> hidden grader tests also check rules that nobody reported. The **contract
> below is the source of truth**.

## Rules

- Don't change `tests/test_reviews.py`.
- Don't open `hidden_tests/` or `SOLUTION/` until you're done.
- Keep `content_checker.find_banned_words` returning `list[str]`, because
  other code depends on it. Fixing its body is fine.
- AI use (to match the OA): one file at a time. Ask it to narrow things down,
  not to rewrite.

## Setup

```bash
pip install -r ../requirements.txt
python manage.py test tests            # the 6 acceptance tests
```

To try it by hand:

```bash
python manage.py migrate
python manage.py seed_demo             # alice = X-User-Id 1, bob = 2, movies 1-6
python manage.py runserver
```

In a second terminal:

```bash
curl -s -H "X-User-Id: 1" "localhost:8000/api/movies/?search=dark"
```

## Project layout

```
reviewsite/            settings + root urls
reviews/
  authentication.py    X-User-Id header auth (works correctly)
  content_checker.py   find_banned_words(text): the existing checker
  models.py            Movie, Review, ReviewerProfile, Violation
  serializers.py       request validation and response shapes
  services.py          moderate(), create_review(), update_review()
  views.py             DRF APIViews
  urls.py              routes
tests/test_reviews.py  the 6 acceptance tests
hidden_tests/          grader's extra tests (spoilers)
SOLUTION/              answer key (spoilers)
```

## API contract

All endpoints need `X-User-Id: <user id>`. Without it you get **401**.

| Method | Path | Body | Success | Errors |
|---|---|---|---|---|
| GET | `/api/movies/?search=<text>` | | 200: movies whose title contains `text`, **case-insensitive**, sorted by title. Without `search`, all movies. | |
| GET | `/api/movies/<id>/reviews/` | | 200: reviews, newest first | 404 |
| POST | `/api/movies/<id>/reviews/` | `{"rating": 1-10, "body"}` | **201**: the review | 400 invalid input; 404 movie; **409** `{"detail": "You have already reviewed this movie."}`; 403 (moderation) |
| PATCH | `/api/reviews/<id>/` | any of `rating`, `body` | 200: the updated review | 404; **403** `{"detail": "You can only edit your own reviews."}`; 403 (moderation) |
| GET | `/api/me/moderation/` | | 200 `{"violation_count", "is_flagged"}` | |

A movie is `{"id", "title", "release_year", "average_rating", "review_count"}`.
A review is `{"id", "movie_id", "author", "rating", "body", "created_at", "updated_at"}`.

## Moderation rules (apply to creating **and** editing a review)

1. A **flagged** user can't post or edit anything, clean or not:
   **403** `{"detail": "Your account is flagged."}`. This doesn't add a
   violation.
2. Otherwise the text being published (for an edit, the **new** body) goes
   through `find_banned_words`. Matching is **case-insensitive**, on whole
   words, and the result is **sorted with no duplicates**.
3. If any banned words are found:
   - respond **403** `{"detail": "Review contains inappropriate language.", "violated_words": [...]}`
   - the review is **not** created or changed
   - the user's `violation_count` goes up by 1 **and is saved**
   - a `Violation` row is stored with the words comma-joined (`"scam,trash"`)
4. When `violation_count` **reaches 3**, the user's `is_flagged` becomes
   `true` (saved).

## Scoring yourself

| Stage | Command | Target |
|---|---|---|
| Acceptance | `python manage.py test tests` | 6/6 |
| Hidden | `python manage.py test hidden_tests` | 6/6 |
