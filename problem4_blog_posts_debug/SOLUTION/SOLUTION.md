# Problem 4: Answer key (spoilers)

The full patch is in `fix.diff`. To apply it from `backend/`:

```bash
patch -p1 < ../SOLUTION/fix.diff
```

## The 15 seeded bugs

### On the path of the 2 visible tests (fix in this order; each one reveals the next)

| # | Where | Bug | Symptom | Fix |
|---|---|---|---|---|
| 1 | `views.py:47` `create_post` | validation uses `title`/`content`/`category` **before** they're read from `request.data`. The `try/except` turns the `UnboundLocalError` into a 500 | `assert 500 == 201`; body `cannot access local variable 'title'...` | move the `if not title...` check below the `data.get(...)` lines |
| 2 | `views.py:84` | returns the model instance: `"post": post` | `TypeError: Object of type Post is not JSON serializable` (no `views.py` frame in the traceback: DRF renders after the view returns) | `"post": serialize_post(post)` |
| 3 | `utils.py:37` `serialize_post` | key is `"id"` (int) instead of `"_id"` (string) | `assert '_id' in {...}` / `KeyError: '_id'` | `"_id": str(post.id)` |
| 4 | `urls.py` | `posts/<str:post_id>/` is listed **before** `posts/my-posts/`, so `my-posts` is routed to `post_detail` with `post_id="my-posts"` | test 2: `assert 500 == 200`; body `Field 'id' expected a number but got 'my-posts'.` | put `my-posts/` first (or use `<int:post_id>`) |
| 5 | `utils.py` `serialize_post` | `excerpt` is missing | `KeyError: 'excerpt'` | add `"excerpt": post.excerpt` |
| 6 | `views.py:61` | `if readTime:` is inverted, so a provided readTime gets overwritten | `assert 1 == 5` | `if not readTime:` |
| 7 | `utils.py:28` `serialize_user` | `"_id": user.id` is an int, but the test sends and expects the string id | `assert 1 == '1'` | `str(user.id)` |
| 8 | `views.py:105-115` `get_my_posts` | builds its own dicts with `"id"` instead of using `serialize_post` | `KeyError: '_id'` in the `found_post` loop (or `assert None is not None` if you patch the dict with `"_id": p.id` and forget `str()`: `12 != '12'`, so nothing matches) | `[serialize_post(p) for p in my_posts]` |

### Hidden-test-only bugs

| # | Where | Bug | Hidden test | Fix |
|---|---|---|---|---|
| 9 | `views.py:58` | `tags = data.get("tags")` passes `None` to a NOT NULL JSONField, giving a 500. This **masks** 3 other hidden tests | `test_tags_default_to_empty_list` (+ unmasks the read-time, ids and invalid-category tests) | `data.get("tags") or []` |
| 10 | `create_post` | no category validation (model `choices` aren't enforced by `objects.create`) | `test_invalid_category_returns_400` | `if category not in VALID_CATEGORIES: return 400 "Invalid category"` (the constant already exists!) |
| 11 | `utils.make_excerpt` | always appends `"..."` (the docstring says only if cut) | `test_excerpt_defaults_from_content` | return `content` unchanged when it's ≤ 150 characters |
| 12 | `views.py:103` `get_my_posts` | `published=True` hides the user's own drafts | `test_my_posts_include_drafts_newest_first` | drop `published=True` |
| 13 | `views.py:32` `list_posts` | public feed doesn't filter `published=True` | `test_public_feed_hides_drafts` | add `.filter(published=True)` |
| 14 | `views.py:137` `get_post` | `DoesNotExist` falls through to the generic `except`, giving a 500 | `test_get_post_by_id_and_missing_post` | catch `Post.DoesNotExist` → 404 `"Post not found"`, like `update_post` does |
| 15 | `utils.is_author` | `post.author_id == user_id` compares an `int` to the header's `str`, so it's **always False**: even the author gets 403 | `test_author_can_update_post`, `test_author_can_delete_post` | `str(post.author_id) == str(user_id)` |

Regression guards (pass on the buggy code, must still pass):
`test_missing_user_header_returns_401`, `test_other_users_cannot_update_or_delete`.
After the visible fixes, `test_missing_required_field_returns_400`,
`test_unknown_user_returns_404` and `test_my_posts_only_show_the_callers_posts`
pass too.

## Red herrings (from the real mock's AI session)

- **`post.save()` after `Post.objects.create(...)`** is redundant but
  harmless. Removing it changes nothing.
- **`readTime` vs `read_time`**: the model field really is camelCase
  `readTime` (`models.py`). Renaming it would break the model, the migration
  and the response. Always open `models.py` before accepting an AI's guess
  about field names.

## Patterns worth remembering

- `try/except Exception: return 500 {"message": str(e)}` **hides tracebacks**.
  The real error is in `response.data`. Print it first.
- Errors raised while **rendering** the response (`not JSON serializable`)
  happen after the view returns, so they bypass the view's `try/except`.
- **Route order**: Django uses the first URL pattern that matches.
  `<str:...>` matches anything, including `my-posts`.
- **Header values are strings.** Compare ids as the same type everywhere
  (`str(...) == str(...)`).
- A copy-pasted serializer (`get_my_posts`) drifts out of sync with the
  shared one. Reuse the helper.
