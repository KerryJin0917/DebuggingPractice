# Problem 1: Answer key (spoilers)

## Hints first (read one at a time)

1. Every test errors before running a single assertion. That isn't the app;
   look at the traceback's file path.
2. The `201` returned by "add movie" comes from the view, but which line in
   `services.add_movie` actually writes a row?
3. Once adding works, the duplicate test may start failing with an
   `IntegrityError` instead of a 409. Read the `.exists()` filter one word at
   a time.
4. `entry.delete` vs `entry.delete()`.
5. Count how many items the bulk loop visits.
6. Hidden tests: compare each status code against the contract table, check
   which fields `.save(update_fields=...)` really saves, ask whether
   `get_watchlist_for_user` ever looks at `user`, and see what DRF does when an
   authentication class has no `authenticate_header`.

## All 12 seeded defects (11 in the app + 1 broken test helper)

| # | File | Bug | Fix | Caught by |
|---|---|---|---|---|
| 0 | `tests/factories.py` | `DEFAULT_GENRE` is used but never defined, so the test module fails to import (**broken fixture, not reported**) | define `DEFAULT_GENRE = "Drama"` (any string) | every visible test |
| 1 | `views.py` `WatchListListCreateView.post` | returns `200` instead of `201` (not reported) | `HTTP_201_CREATED` | `test_create_watchlist_returns_201_and_persists` |
| 2 | `services.add_movie` | `WatchListEntry(...)` is built but never saved (**QA #1**) | `WatchListEntry.objects.create(...)` | `test_add_movie_to_watchlist_persists`, `..._409`, `test_bulk_add_then_remove` |
| 3 | `views.py` `WatchListMoviesView.post` | calls `services.get_watchlist_for_user` directly, so `None` reaches `add_movie` and `None.id` raises a 500 (**QA #2**) | use `_load_watchlist(...)` like the other views | `test_add_movie_to_missing_watchlist_returns_404` |
| 4 | `services.add_movie` | duplicate check filters `movie_id=watchlist.id` (wrong variable), so duplicates reach the DB unique constraint and raise `IntegrityError` (not reported) | `filter(watchlist=watchlist, movie=movie)` | `test_add_duplicate_movie_returns_409` |
| 5 | `services.remove_movie` | `entry.delete` without parentheses never runs (**QA #3**) | `entry.delete()` | `test_remove_movie_from_watchlist` |
| 6 | `services.bulk_update_movies` | `range(1, len(add_ids))` skips the first id, an off-by-one (not reported) | `for movie_id in add_ids:` | `test_bulk_add_then_remove` |
| 7 | `services.update_watchlist` | `save(update_fields=["description", "updated_at"])` drops `name`. The response looks right because it serializes the in-memory object, but the DB never changes | add `"name"` to `update_fields` | hidden `test_update_watchlist_name_persists` |
| 8 | `views.py` `WatchListDetailView.delete` | returns `200` with a body instead of `204` | `Response(status=HTTP_204_NO_CONTENT)` | hidden `test_delete_watchlist_returns_204` |
| 9 | `services.get_watchlist_for_user` | ignores `user`, so anyone can read, delete, or edit anyone's list (IDOR) | `filter(pk=watchlist_id, owner=user)` | hidden `test_cannot_read_or_delete_another_users_watchlist` |
| 10 | `authentication.py` | no `authenticate_header()`, so DRF turns `NotAuthenticated` into **403** instead of 401 | add `def authenticate_header(self, request): return self.header` | hidden `test_unauthenticated_request_returns_401` |
| 11 | `serializers.py` | `name = CharField(..., allow_blank=True)` accepts `"   "` | drop `allow_blank=True` (DRF trims whitespace by default) | hidden `test_blank_name_is_rejected` |

Two hidden tests (`test_add_unknown_movie_returns_404`,
`test_bulk_with_unknown_movie_applies_nothing`) are **regression guards**.
They pass on the buggy code and must still pass after your fixes. For
example, if you "fix" bulk by catching `NotFound` per movie, you break the
all-or-nothing rule.

The full patch is in `fix.diff` (`patch -p1 < SOLUTION/fix.diff` from this
folder).

## Takeaways

- **Fix the harness first.** When every test fails the same way, the bug is
  usually in shared setup, not in each feature.
- **"Says success but nothing changed"** almost always means a missing
  `.save()` / `.create()`, a method referenced without being called, or a
  `save(update_fields=...)` that leaves out the field.
- **Responses can lie.** A view that serializes the in-memory object shows
  the new value even when the DB write was skipped. Assert against the DB
  (`refresh_from_db`).
- **Fixing one bug can reveal the next.** Bug 2 hides bug 4: duplicates only
  reach the database once adds actually persist.
- **Status codes are part of the contract.** Check every 200/201/204/401/403
  against the README table.
