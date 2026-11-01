# 02: Problem 1 walkthrough (watch-list debugging)

> ⚠️ Full spoilers for `problem1_watchlist_debug/`. All commands run from that
> folder. Output is from real runs, with paths shortened.

Goal: clear **6/6 visible** tests, then use the contract to find the bugs
behind the **7 hidden** tests. We'll use the loop from `01_method.md` for
each bug: **Reproduce → Locate → Isolate → Patch → Verify**.

---

## Phase 0: Orient (≈5 min)

Read `README.md`. Notes worth writing down from the contract:

- Missing header → **401**. Someone else's list → **404**, "never visible or editable".
- `POST /api/watchlists/` → **201**. `DELETE` list → **204**, empty body.
- Add movie: **201**, or 404 / 404 / **409** with exact messages.
- Bulk: adds first, then removes; unknown id → 404 and **nothing changes**.

The QA report lists 3 bugs, and the README warns there are more. Request
path: `movies/urls.py → movies/views.py → movies/services.py`.

Run everything:

```bash
python manage.py test tests
```

```
ERROR: tests.test_watchlists (unittest.loader._FailedTest.tests.test_watchlists)
ImportError: Failed to import test module: tests.test_watchlists
  File "tests/test_watchlists.py", line 9, in <module>
    from .factories import auth, make_movie, make_user, make_watchlist
  File "tests/factories.py", line 11, in <module>
    def make_movie(title="Inception", genre=DEFAULT_GENRE, release_year=2010):
                                            ^^^^^^^^^^^^^
NameError: name 'DEFAULT_GENRE' is not defined

Ran 1 test in 0.001s
```

"Ran **1** test" when there should be 6 means the test module didn't even
import. **Fix the harness first.**

## Bug 0: broken test helper (not in the QA list)

| Step | |
|---|---|
| Reproduce | The import error above |
| Locate | The traceback's lowest project frame: `tests/factories.py:11` |
| Isolate | `DEFAULT_GENRE` is used as a default argument but defined nowhere (`grep -rn DEFAULT_GENRE .` finds only this line) |
| Patch | Define it above the function. The value doesn't matter: every test passes `genre` explicitly. Assertions aren't touched. |

```python
DEFAULT_GENRE = "Drama"


def make_movie(title="Inception", genre=DEFAULT_GENRE, release_year=2010):
```

Verify by re-running the suite. Now 6 tests run:

```
ERROR: test_add_movie_to_missing_watchlist_returns_404
AttributeError: 'NoneType' object has no attribute 'id'
FAIL: test_add_duplicate_movie_returns_409
AssertionError: 201 != 409
FAIL: test_add_movie_to_watchlist_persists
AssertionError: Lists differ: [] != ['Arrival']
FAIL: test_bulk_add_then_remove
AssertionError: 0 != 3
FAIL: test_create_watchlist_returns_201_and_persists
AssertionError: 200 != 201
FAIL: test_remove_movie_from_watchlist
AssertionError: Lists differ: ['Inception', 'Parasite'] != ['Parasite']
Ran 6 tests in 0.069s
FAILED (failures=5, errors=1)
```

### Triage

| Test | Symptom | Bucket | Order |
|---|---|---|---|
| `create_..._201` | `200 != 201` | status code, one-liner | 1 |
| `missing_watchlist_404` | `AttributeError` (500) | crash, traceback points at it | 2 |
| `add_movie_..._persists` | `[] != ['Arrival']` | "said success, nothing saved" (QA #1) | 3 |
| `duplicate_409` | `201 != 409` | probably shares the add path with #3 | 4 |
| `remove_movie` | entry still there | "said 204, nothing deleted" (QA #3) | 5 |
| `bulk` | `0 != 3` | shares the add path, re-check after #3 | 6 |

Notice that three tests go through `services.add_movie`. Fixing it might
change several results at once, so **re-run the whole suite after it**.

---

## Bug 1: create returns 200

- **Reproduce:** `python manage.py test tests -k create`. Output: `AssertionError: 200 != 201`.
- **Locate:** no traceback, so follow the path: `POST /api/watchlists/` → `WatchListListCreateView.post`.
  `grep -n "status=" movies/views.py` shows the candidates fast.
- **Isolate:** `movies/views.py:41`, `status=status.HTTP_200_OK` on a create. The contract says 201.
- **Patch:**
  ```diff
  -        return Response(WatchListSerializer(watchlist).data, status=status.HTTP_200_OK)
  +        return Response(WatchListSerializer(watchlist).data, status=status.HTTP_201_CREATED)
  ```
- **Verify:** `-k create` passes. The test also checks the DB and the list endpoint, so creating really works.

> Also note `movies/views.py:59` (DELETE returns 200 with a body). No visible
> test covers it, but the contract says 204. Put it on your audit list for
> later.

## Bug 2: adding to a missing list crashes (QA #2)

- **Reproduce:** `python manage.py test tests -k missing`
- **Locate:** read the traceback bottom-up and stop at the lowest frame in our code:
  ```
  File "movies/views.py", line 67, in post
      services.add_movie(watchlist, serializer.validated_data["movie_id"])
  File "movies/services.py", line 45, in add_movie
      if WatchListEntry.objects.filter(watchlist=watchlist, movie_id=watchlist.id).exists():
  AttributeError: 'NoneType' object has no attribute 'id'
  ```
  The crash is in `services.py:45`, but **the cause is upstream**: why is
  `watchlist` `None`?
- **Isolate:** `WatchListMoviesView.post` (`views.py:64`) calls
  `services.get_watchlist_for_user(...)` directly. That function returns
  `None` when nothing matches. Every *other* view calls `_load_watchlist()`,
  which turns `None` into `NotFound("Watch list not found.")`. This view is
  the odd one out.
- **Patch** (follow the existing pattern):
  ```diff
  -        watchlist = services.get_watchlist_for_user(request.user, watchlist_id)
  +        watchlist = _load_watchlist(request, watchlist_id)
  ```
- **Verify:** `-k missing` passes. It also checks the exact `detail` string,
  which `_load_watchlist` already produces.

> 💡 While you're on line 45, notice `movie_id=watchlist.id`. That looks
> wrong too. Don't fix it yet: one bug at a time keeps your test signal clean.
> Note it.

## Bug 3: added movie never persists (QA #1)

- **Reproduce:** `python manage.py test tests -k to_watchlist_persists`. Output: `Lists differ: [] != ['Arrival']`. The API said 201 but the list is empty.
- **Locate:** `services.add_movie` (`services.py:43`).
- **Isolate:** "said success, nothing saved" → look for the write:
  ```python
  entry = WatchListEntry(watchlist=watchlist, movie=movie)   # line 47
  return entry
  ```
  `Model(...)` only builds an object in memory. Nothing ever calls `.save()`.
  (Running with `-d` would show no `INSERT` for `movies_watchlistentry`.)
- **Patch:**
  ```diff
  -    entry = WatchListEntry(watchlist=watchlist, movie=movie)
  +    entry = WatchListEntry.objects.create(watchlist=watchlist, movie=movie)
  ```
- **Verify, with the whole suite.** Three tests use this path, so:
  ```bash
  python manage.py test tests -k duplicate -k bulk
  ```
  ```
  ERROR: test_add_duplicate_movie_returns_409
  django.db.utils.IntegrityError: UNIQUE constraint failed: movies_watchlistentry.watchlist_id, movies_watchlistentry.movie_id
    File "movies/services.py", line 47, in add_movie
  FAIL: test_bulk_add_then_remove
  AssertionError: 2 != 3
  ```
  **Both changed**, and that's progress. The duplicate test went from
  `201 != 409` to an `IntegrityError`, and bulk went from `0 != 3` to
  `2 != 3`. Fixing bug 3 **unmasked** two more bugs. Before, nothing was
  saved, so the duplicate check never mattered and bulk added zero.

## Bug 4: duplicate check uses the wrong variable

- **Reproduce:** `-k duplicate`. The second insert reaches the DB unique
  constraint, so the duplicate check above it didn't catch it.
- **Isolate:** the line you noted earlier, `services.py:45`:
  ```python
  WatchListEntry.objects.filter(watchlist=watchlist, movie_id=watchlist.id).exists()
  ```
  It asks "is the movie whose id equals *this watch list's id* already in the
  list?" That's the wrong variable.
  (Sneaky detail: when the watch list's id happens to equal the movie's id,
  the buggy check works. The test adds the 2nd movie to the 1st list to avoid
  that coincidence.)
- **Patch:**
  ```diff
  -    if WatchListEntry.objects.filter(watchlist=watchlist, movie_id=watchlist.id).exists():
  +    if WatchListEntry.objects.filter(watchlist=watchlist, movie=movie).exists():
  ```
- **Verify:** `-k duplicate` passes (409 + exact message + only one row).

## Bug 5: remove does nothing (QA #3)

- **Reproduce:** `-k remove_movie`. Output: `['Inception', 'Parasite'] != ['Parasite']`. It said 204, but nothing was deleted.
- **Locate:** `services.remove_movie`, `services.py:51`.
- **Isolate:** `services.py:55` is `entry.delete`. It names the method but
  never **calls** it. Python evaluates the bound method and throws it away,
  with no error.
- **Patch:** `entry.delete()`
- **Verify:** `-k remove_movie` passes.

## Bug 6: bulk skips the first id (off-by-one)

- **Reproduce:** `-k bulk`. Output: `2 != 3`. Three ids were sent and two were added.
- **Isolate:** `services.py:66`:
  ```python
  for i in range(1, len(add_ids)):   # visits indices 1..n-1, so index 0 is skipped
      movie_id = add_ids[i]
  ```
  Check the count: 3 ids, `range(1, 3)` → 2 iterations. Off by one.
- **Patch** (and simplify, since the index isn't needed):
  ```diff
  -    for i in range(1, len(add_ids)):
  -        movie_id = add_ids[i]
  +    for movie_id in add_ids:
  ```
- **Verify, whole suite:**
  ```
  Ran 6 tests in 0.07s
  OK
  ```

**6/6 visible.** In a real OA you'd be at roughly 25–35 minutes here. Don't
stop: hidden tests count.

---

## Phase 2: Contract audit for hidden bugs

Go through the README contract row by row. For each line, find the code that
implements it and ask whether a visible test covers it.

| Contract line | Code | Visible test? | Looks right? |
|---|---|---|---|
| Missing header → 401 | `authentication.py`, DRF default permissions | no | **unknown**: probe |
| Others' lists → 404, never visible | `services.get_watchlist_for_user` | no | **suspicious**: the `user` param is never used! |
| POST name missing/blank → 400 | `serializers.py:13` `allow_blank=True` | no | **suspicious** |
| PATCH → changes saved to DB | `services.update_watchlist` | no | **suspicious**: `update_fields` |
| DELETE → 204, empty body | `views.py:59` | no | **wrong** (noted earlier) |
| Unknown movie → 404 "Movie not found." | `services.get_movie` | no | looks fine |
| Bulk all-or-nothing | `@transaction.atomic` + `get_movie` raising | no | looks fine |

Instead of guessing, **write throwaway probe tests** straight from the
contract. Create `tests/test_probe.py`:

```python
"""Scratch probes written from the README contract. Delete before submitting."""
from django.test import TestCase

from .factories import auth, make_user, make_watchlist


class ContractProbes(TestCase):
    def setUp(self):
        self.alice = make_user("alice")
        self.bob = make_user("bob")
        self.wl = make_watchlist(self.alice, name="Weekend")
        self.url = f"/api/watchlists/{self.wl.pk}/"

    def test_no_header_is_401(self):
        self.assertEqual(self.client.get("/api/watchlists/").status_code, 401)

    def test_patch_name_is_saved_to_db(self):
        self.client.patch(self.url, {"name": "Rainy"}, content_type="application/json", **auth(self.alice))
        self.wl.refresh_from_db()
        self.assertEqual(self.wl.name, "Rainy")

    def test_delete_is_204(self):
        self.assertEqual(self.client.delete(self.url, **auth(self.alice)).status_code, 204)

    def test_other_user_gets_404(self):
        self.assertEqual(self.client.get(self.url, **auth(self.bob)).status_code, 404)

    def test_blank_name_is_400(self):
        r = self.client.post("/api/watchlists/", {"name": "  "}, content_type="application/json", **auth(self.alice))
        self.assertEqual(r.status_code, 400)
```

```bash
python manage.py test tests.test_probe
```

```
FAIL: test_blank_name_is_400        AssertionError: 201 != 400
FAIL: test_delete_is_204            AssertionError: 200 != 204
FAIL: test_no_header_is_401         AssertionError: 403 != 401
FAIL: test_other_user_gets_404      AssertionError: 200 != 404
FAIL: test_patch_name_is_saved_to_db AssertionError: 'Weekend' != 'Rainy'
```

That's five probes and five real bugs, found in about 3 minutes. Now loop
over each one.

## Bug 7: PATCH response lies, DB unchanged

- **Isolate:** `services.py:35`:
  ```python
  watchlist.save(update_fields=["description", "updated_at"])
  ```
  `update_fields` means "write **only** these columns". `name` is set on the
  Python object but never written. The API response still shows the new name
  because the view serializes the in-memory object. That's why only a
  `refresh_from_db()` assertion catches it.
- **Patch:** `update_fields=["name", "description", "updated_at"]` (or just `watchlist.save()`).

## Bug 8: DELETE returns 200 with a body

- **Patch** `views.py:59`:
  ```diff
  -        return Response({"detail": "Watch list deleted."}, status=status.HTTP_200_OK)
  +        return Response(status=status.HTTP_204_NO_CONTENT)
  ```

## Bug 9: any user can access anyone's list (IDOR)

- **Isolate:** `services.py:15–17`:
  ```python
  def get_watchlist_for_user(user, watchlist_id):
      return WatchList.objects.filter(pk=watchlist_id).first()
  ```
  The parameter `user` is **never used**, which is a big smell. Because every
  view loads lists through this function, one fix covers GET, PATCH, DELETE,
  add, remove, and bulk.
- **Patch:** `filter(pk=watchlist_id, owner=user)`. It returns `None` for
  other users' lists, and `_load_watchlist` turns that into the same 404 as
  "doesn't exist", so it doesn't leak that the list exists.

## Bug 10: unauthenticated → 403 instead of 401

- **Isolate:** this is a DRF framework rule, not a typo. When a request
  isn't authenticated, DRF asks the first authentication class for
  `authenticate_header()`, the value of the `WWW-Authenticate` response
  header. If the class doesn't define one (the base class returns `None`),
  DRF answers **403**. `HeaderUserAuthentication` doesn't define it.
- **Patch** `authentication.py`:
  ```python
  def authenticate_header(self, request):
      return self.header
  ```

## Bug 11: blank name accepted

- **Isolate:** `serializers.py:13`, `CharField(max_length=100, allow_blank=True)`.
  DRF trims whitespace by default, so `"   "` becomes `""`, and
  `allow_blank=True` lets that through.
- **Patch:** remove `allow_blank=True`.

## Finish

```bash
rm tests/test_probe.py                       # don't ship scratch files
python manage.py test tests hidden_tests
```

```
Ran 13 tests
OK
```

Then review `git diff`. It should be about a dozen small hunks, each mapping
to one bug above, plus the `DEFAULT_GENRE` line in `factories.py`, and no
stray `print` or `breakpoint()`.

---

## What to take away

1. **Harness first.** "Ran 1 test" with an `ImportError` means nothing ran at all.
2. **The crash frame isn't always the bug.** Bug 2 crashed in `services.py`,
   but the cause was the view skipping `_load_watchlist`.
3. **Follow the codebase's pattern.** The view that's different from the
   others is often the bug.
4. **Fixes unmask bugs.** Re-run the whole suite after each fix. A test
   whose *error message changes* is progress, not a regression.
5. **"Success but nothing happened"** → missing `.save()`/`.create()`, a
   method not called (`delete` vs `delete()`), or `update_fields` leaving out
   the column.
6. **Unused parameters are a smell.** `user` in `get_watchlist_for_user`
   pointed straight at an authorization hole.
7. **Probe the contract.** Five 3-line tests found every hidden bug faster
   than reading the code would have.
