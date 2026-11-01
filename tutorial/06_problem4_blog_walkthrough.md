# 06: Problem 4 walkthrough (blog "Create Post", modeled on the mock OA)

> ⚠️ Full spoilers for `problem4_blog_posts_debug/`. Commands run from
> `problem4_blog_posts_debug/backend/`. All output is from real runs.

This problem copies the HackerRank mock: a Django + DRF blog, **2 visible
tests**, and 15 hidden ones. The 2 visible tests run through 8 bugs in
sequence: each fix moves the failure to the next line. Then the hidden suite
grades everything else in the README.

---

## pytest commands for this OA format

The mock ran tests with **pytest**, not `manage.py test`. These are the flags
that matter:

| Command | Use it for |
|---|---|
| `python -m pytest blog/tests.py` | run the visible tests (plain `pytest` works too if it's the same Python) |
| `python -m pytest blog/tests.py -q` | quiet: one line per failure in the summary |
| `python -m pytest blog/tests.py -x` | stop at the first failure |
| `python -m pytest blog/tests.py -k save_created` | run only tests whose name contains `save_created` |
| `python -m pytest blog/tests.py --tb=short` | shorter tracebacks |
| `python -m pytest blog/tests.py -vv` | full assertion diffs (long dicts/lists) |
| `python -m pytest blog/tests.py -x --pdb` | open the debugger at the failing assertion |
| `python -m pytest blog/tests.py -s` | show your `print()` output (pytest hides it by default) |
| `python -m pytest blog/tests.py -p no:logging` | hide the "Captured log call: Internal Server Error" noise |

In pytest, `assert a == b` prints **`assert <actual> == <expected>`** the way
the test wrote it, so read the test line to know which side is which.

---

## The trap in this codebase: a `try/except` that swallows errors

Every view looks like this:

```python
def create_post(request):
    try:
        ...
    except Exception as e:
        return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
```

So a crash **doesn't** produce a traceback in the test output. You just see
`assert 500 == 201`. **The real error is in `response.data["message"]`.**
Getting that message is always step one. This is what took the most time in
the mock: the AI guessed at causes for several rounds because nobody had
printed the error message yet.

---

## Round 1: `assert 500 == 201` → get the message

```bash
python -m pytest blog/tests.py -q -p no:logging
```
```
FAILED blog/tests.py::test_create_post_with_expected_response_structure_and_values
FAILED blog/tests.py::test_save_created_post_to_database - assert 500 == 201
2 failed in 0.21s
```

Open the debugger at the failure and print the response body:

```bash
python -m pytest blog/tests.py -x -p no:logging --pdb
```
```
>       assert response.status_code == 201
E       assert 500 == 201
...
-> assert response.status_code == 201
(Pdb) p response.data
{'message': "cannot access local variable 'title' where it is not associated with a value"}
(Pdb) q
```

(No debugger in the OA IDE? Add `print(response.data)` above the failing
line and run with `-s`. Remove it afterwards: you may not edit tests, so
make sure it's gone before you submit.)

- **Locate:** `grep -n "title" blog/views.py`. Line 47 uses `title` and line
  54 assigns it:
  ```python
  47        if not title or not content or not category:      # used here...
  ...
  53        data = request.data
  54        title = data.get("title")                           # ...assigned here
  ```
- **Patch:** move the `if not title ...` block below the `data.get(...)` lines.
- **Verify:**

```
E       TypeError: Object of type Post is not JSON serializable
FAILED blog/tests.py::test_create_post_with_expected_response_structure_and_values
FAILED blog/tests.py::test_save_created_post_to_database - TypeError: Object ...
```

## Round 2: `Object of type Post is not JSON serializable`

```bash
python -m pytest blog/tests.py -x -q -p no:logging --tb=short
```
```
blog/tests.py:37: in test_create_post_with_expected_response_structure_and_values
/usr/local/lib/python3.13/json/__init__.py:242: in dumps
/usr/local/lib/python3.13/json/encoder.py:202: in encode
...
E   TypeError: Object of type Post is not JSON serializable
```

There's **no `views.py` frame**, and the view's `try/except` didn't catch
it. DRF turns the `Response` into JSON **after** the view returns, so
something the view put in the `Response` is a model object. Search for it:

```bash
grep -n "Response(" blog/views.py | grep -v message
grep -n '"post": post' blog/views.py
```

`views.py:84` has `{"message": "Post created successfully", "post": post}`.
There's already a helper for this: `serialize_post` in `blog/utils.py`
(already imported in `views.py`).

- **Patch:** `"post": serialize_post(post)`
- **Verify:**

```
E       AssertionError: assert '_id' in {'id': 1, 'title': 'Debugging Django Like a Pro', ...}
E       KeyError: '_id'
```

## Round 3: `'_id' in {'id': 1, ...}`: wrong key in the shared serializer

The test wants `_id` (the Mongo-style key from the README). `utils.py:37`
has `"id": post.id`. The README also says ids are **strings**.

- **Patch:** `"_id": str(post.id),`
- **Verify:**

```
E       KeyError: 'excerpt'
E       assert 500 == 200
FAILED blog/tests.py::test_create_post_with_expected_response_structure_and_values
FAILED blog/tests.py::test_save_created_post_to_database - assert 500 == 200
```

Test 2 got further: creation works, and now the **My Posts** request
returns 500. Two different failures means take them one at a time. Start
with test 2's new 500, since it's a different file.

## Round 4: My Posts returns 500 → the URL goes to the wrong view

Get the message the same way, at a different line:

```bash
python -m pytest blog/tests.py -k save_created -p no:logging --pdb
```
```
-> assert user_posts_response.status_code == 200
(Pdb) p user_posts_response.data
{'message': "Field 'id' expected a number but got 'my-posts'."}
```

"`'my-posts'` used as an id" means the request reached the **detail** view.
Ask Django which view a URL resolves to:

```bash
python manage.py shell -v 0 -c "from django.urls import resolve; m = resolve('/api/posts/my-posts/'); print(m.view_name, m.kwargs)"
```
```
post-detail {'post_id': 'my-posts'}
```

`blog/urls.py` lists `posts/<str:post_id>/` **before** `posts/my-posts/`.
Django uses the first pattern that matches, and `<str:>` matches anything.

- **Patch:** move the `my-posts/` line above the `<str:post_id>/` line.
- **Verify:** the same command now prints `my-posts {}`, and the suite shows:

```
E       KeyError: 'excerpt'
E           KeyError: '_id'
```

## Round 5: `KeyError: 'excerpt'`

`serialize_post` has no `excerpt` key (compare it with the README's post
object).

- **Patch:** add `"excerpt": post.excerpt,` to `serialize_post`.
- **Verify:**

```
E       assert 1 == 5
E           KeyError: '_id'
```

## Round 6: `assert 1 == 5`: readTime overwritten

```
        assert post["tags"] == post_data["tags"]
>       assert post["readTime"] == post_data["readTime"]
E       assert 1 == 5
```

The test **sent** `readTime: 5` and got back 1 (the computed default for a
10-word post). `views.py:61` reads `if readTime: readTime = calculate_read_time(content)`.
It's inverted: it recalculates exactly when a value **was** provided.

- **Patch:** `if not readTime:`
- **Verify:**

```
E       AssertionError: assert 1 == '1'
E           KeyError: '_id'
```

## Round 7: `assert 1 == '1'`: int vs string id

```
>       assert post["author"]["_id"] == user_id
E       AssertionError: assert 1 == '1'
```

The test's `user_id` is `str(test_user.id)`, the same string it sends in the
header. `serialize_user` (`utils.py:28`) returns `user.id`, an int. (This is
the str-vs-int question Gemini kept going back and forth on. The assertion
answers it in one line.)

- **Patch:** `"_id": str(user.id),`
- **Verify:**

```
E           KeyError: '_id'
FAILED blog/tests.py::test_save_created_post_to_database - KeyError: '_id'
1 failed, 1 passed
```

**Test 1 passes.**

## Round 8: My Posts items have no `_id`

```
        found_post = None
        for post in user_posts_response.data["posts"]:
>           if post["_id"] == created_post_id:
E           KeyError: '_id'
```

`get_my_posts` (`views.py:105-115`) builds its own dicts with `"id": p.id`
instead of using `serialize_post`. Copy-paste drift.

- **Patch:** `return Response({"posts": [serialize_post(p) for p in my_posts]}, status=status.HTTP_200_OK)`
- ⚠️ If you instead just rename the key to `"_id": p.id`, you get
  `assert None is not None`. `12 != '12'`, so the loop never matches. That's
  the exact failure from the mock.
- **Verify:**

```
2 passed
```

**2/2 visible**, after 8 bugs in 4 files: `views.py`, `utils.py`, `urls.py`,
and back to `views.py`.

---

## Round 9: The hidden suite

```bash
python -m pytest hidden_tests -q -p no:logging
```
```
FAILED hidden_tests/test_hidden_posts.py::test_invalid_category_returns_400        (assert 500 == 400)
FAILED hidden_tests/test_hidden_posts.py::test_read_time_defaults_from_word_count  (assert 500 == 201)
FAILED hidden_tests/test_hidden_posts.py::test_tags_default_to_empty_list          (assert 500 == 201)
FAILED hidden_tests/test_hidden_posts.py::test_excerpt_defaults_from_content       (KeyError: 'post')
FAILED hidden_tests/test_hidden_posts.py::test_ids_are_strings                     (KeyError: 'post')
FAILED hidden_tests/test_hidden_posts.py::test_my_posts_include_drafts_newest_first
FAILED hidden_tests/test_hidden_posts.py::test_public_feed_hides_drafts
FAILED hidden_tests/test_hidden_posts.py::test_get_post_by_id_and_missing_post     (assert 500 == 404)
FAILED hidden_tests/test_hidden_posts.py::test_author_can_update_post              (assert 403 == 200)
FAILED hidden_tests/test_hidden_posts.py::test_author_can_delete_post              (assert 403 == 200)
10 failed, 5 passed
```

In the real OA you **can't see these**, so you'd find them by auditing the
README contract against the code. Here's that audit, rule by rule:

| README rule | Code | Problem |
|---|---|---|
| `tags` defaults to `[]` | `tags = data.get("tags")` | `None` hits a NOT NULL column, so 500 for **every post without tags**. That's why 4 hidden tests show 500 or `KeyError: 'post'` |
| invalid category → 400 | no check in `create_post` (the model's `choices` aren't enforced by `objects.create`) | add `if category not in VALID_CATEGORIES` (the constant is already defined at the top of `views.py`) |
| excerpt: `"..."` only if cut | `make_excerpt` always appends `"..."` | return `content` unchanged when ≤ 150 characters |
| My Posts includes drafts | `filter(author_id=user_id, published=True)` | drop `published=True` |
| public feed: published only | `list_posts` has no `published` filter | add `.filter(published=True)` |
| `GET /posts/<id>/` missing → 404 | `get_post` lets `DoesNotExist` reach the generic `except` (500) | catch `Post.DoesNotExist` like `update_post` does |
| only the author may edit/delete | `is_author`: `post.author_id == user_id` compares **int to str**, so it's always False and **even the author gets 403** | `str(post.author_id) == str(user_id)` |

A fast way to probe these without the hidden tests: a 10-line scratch test,
or `curl` against `runserver`:

```bash
curl -s -X POST localhost:8000/api/posts/ -H "X-User-Id: 1" -H "Content-Type: application/json" \
     -d '{"title": "No tags", "content": "Hello", "category": "food"}'
# {"message":"NOT NULL constraint failed: blog_post.tags"}
```

After those 7 fixes:

```bash
python -m pytest blog/tests.py hidden_tests -q -p no:logging
```
```
17 passed
```

---

## Lessons from the actual mock session

1. **Print the error before theorizing.** For the first several rounds, the
   AI produced plausible causes (`read_time` naming, `post.save()`, missing
   `return`) without seeing the real error. One `p response.data` would have
   shown `cannot access local variable 'title'` immediately.
2. **Don't accept field-name guesses. Open `models.py`.** The field really
   was `readTime`. Renaming it to the "conventional" `read_time` would have
   added a bug.
3. **Feed the AI evidence, not descriptions:** the failing assertion line,
   the actual `response.data`, and the relevant function. It only sees the
   open file.
4. **Each failure message is a checkpoint.** `500` → `not JSON serializable`
   → `KeyError '_id'` → `KeyError 'excerpt'` → `1 == 5` → `1 == '1'` →
   `None is not None`. A *new* message means progress, not a new problem.
5. **Look outside `views.py`.** In this repo the visible-test bugs are spread
   across `utils.py` and `urls.py`, and the hidden ones across helpers too.
6. **With 2 visible tests, most of the score is hidden.** Save 15+ minutes to
   go through the README contract against every endpoint.
