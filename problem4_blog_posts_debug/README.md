# Problem 4: Blog "Create Post" (debugging only, modeled on the mock OA)

**Time limit: 60 minutes.** This one copies the format of the HackerRank mock
assessment: a Django + DRF blog backend, **only 2 visible tests**, and a much
larger hidden suite that grades the rest of the contract.

## Task

Users report that clicking **Publish** in the blog editor fails, and
nothing shows up under **My Posts**. Repair `POST /api/posts/` so that it:

- reads the fields from `request.data`
- requires `title`, `content` and `category`
- generates defaults for the optional fields (`excerpt`, `tags`, `readTime`)
- associates the saved post with the user identified by the `X-User-Id` header
- returns **HTTP 201** with the expected JSON structure, including `_id` and a nested `author`
- makes the new post appear under **My Posts** (`GET /api/posts/my-posts/`)

The acceptance tests are in `backend/blog/tests.py`:

- `test_create_post_with_expected_response_structure_and_values`
- `test_save_created_post_to_database`

> The hidden tests also cover the other endpoints in the API reference
> below. Bugs can be in any file under `backend/blog/`, not only `views.py`.

## Rules

- Don't change `backend/blog/tests.py`.
- Don't open `backend/hidden_tests/` or `SOLUTION/` until you're done.
- AI use (to match the OA): the assistant only sees the file you have open.
  Give it the failing assertion **and the actual response body**. Don't let
  it guess field names it can't see.

## Setup and running tests

```bash
pip install -r ../requirements.txt          # Django, DRF, pytest, pytest-django
cd backend
python -m pytest blog/tests.py               # the 2 visible tests (plain `pytest` works too)
python -m pytest blog/tests.py -x --pdb      # stop at the first failure in the debugger
python -m pytest hidden_tests                # the grader's tests, when you're done
```

To try it by hand:

```bash
python manage.py migrate
python manage.py shell -c "import blog.seed"     # prints X-User-Id values for alice and bob
python manage.py runserver
```

In a second terminal:

```bash
curl -s -X POST localhost:8000/api/posts/ -H "X-User-Id: 1" -H "Content-Type: application/json" \
     -d '{"title": "Hi", "content": "Hello world", "category": "technology"}'
```

## Project layout (same shape as the mock)

```
backend/
  manage.py
  pytest.ini
  blog_backend/      settings.py, urls.py
  blog/
    middleware.py    UserIdMiddleware: X-User-Id header → request.user_id
    models.py        User, Post, CATEGORY_CHOICES
    utils.py         serializers (serialize_post / serialize_user) and helpers
    views.py         function-based DRF views
    urls.py          routes
    tests.py         the 2 visible tests
  hidden_tests/      grader's tests (spoilers)
```

## API reference

Every write needs `X-User-Id: <user id>`. Ids are **strings** in responses,
because the API was ported from MongoDB and the frontend still expects that.

**Post object**

```json
{
  "_id": "12",
  "title": "string",
  "content": "string",
  "excerpt": "string",
  "category": "technology",
  "tags": ["string"],
  "readTime": 5,
  "published": true,
  "author": {"_id": "3", "name": "string", "email": "string", "bio": "string"},
  "createdAt": "ISO-8601",
  "updatedAt": "ISO-8601"
}
```

**`POST /api/posts/`**: request body:

```json
{"title": "string", "content": "string", "excerpt": "string",
 "category": "string", "tags": ["string"], "readTime": 5}
```

| Case | Response |
|---|---|
| success | **201** `{"message": "Post created successfully", "post": <post>}` |
| no `X-User-Id` | 401 `{"message": "Not authenticated"}` |
| missing `title`, `content` or `category` | 400 `{"message": "Title, content, and category are required"}` |
| `category` not one of `technology, lifestyle, travel, food, health, business, other` | 400 `{"message": "Invalid category"}` |
| user doesn't exist | 404 `{"message": "User not found"}` |

Defaults for omitted optional fields:

- `excerpt`: the content, cut to 150 characters plus `"..."` **only if it was longer than 150**
- `tags`: `[]`
- `readTime`: `max(1, words // 200)` (about 200 words per minute)
- `published`: `true`

**Other endpoints**

| Method | Path | Success | Errors |
|---|---|---|---|
| GET | `/api/posts/?category=` | 200 `{"posts": [...]}`: **published** posts only, newest first | |
| GET | `/api/posts/my-posts/` | 200 `{"posts": [...]}`: the caller's posts **including drafts**, newest first | 401 |
| GET | `/api/posts/<id>/` | 200 `{"post": <post>}` | 404 `{"message": "Post not found"}` |
| PUT | `/api/posts/<id>/` | 200 `{"message": "Post updated successfully", "post": <post>}` | 404; 403 `{"message": "Not authorized"}` unless the caller is the author; 400 invalid category |
| DELETE | `/api/posts/<id>/` | 200 `{"message": "Post deleted successfully"}` | 404; 403 `{"message": "Not authorized"}` |

## Scoring yourself

| Stage | Command (from `backend/`) | Target |
|---|---|---|
| Visible | `python -m pytest blog/tests.py` | 2/2 |
| Hidden | `python -m pytest hidden_tests` | 15/15 |

A full solve with real output at every step is in
[`../tutorial/06_problem4_blog_walkthrough.md`](../tutorial/06_problem4_blog_walkthrough.md)
(spoilers).
