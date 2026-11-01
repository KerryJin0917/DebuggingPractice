# Problem 3: Answer key (spoilers)

The full patch is in `fix.diff`. To apply it from this folder:

```bash
patch -p1 < SOLUTION/fix.diff
```

A step-by-step solve, with the debugger session for each bug, is in
`../tutorial/05_debugging_loop_step_by_step.md`, Part B.

## All 10 seeded defects

| # | File | Bug | Fix | Ticket / test |
|---|---|---|---|---|
| 1 | `views.py` `MovieListView` | reads `query_params.get("q")`, but the contract's parameter is `search`, so the filter never runs | `.get("search")` | Ticket 1, `test_search_movies_...` |
| 2 | `serializers.py` | `rating = IntegerField(min_value=1, max_value=5)`, but the contract says 1–10. Any rating above 5 → 400. This **masks** 3 other tests, which all fail with 400 at first | `max_value=10` | Ticket 2, `test_create_clean_review_returns_201` (+ 3 masked) |
| 3 | `services.moderate` | `violation_count += 1` but the profile is never saved | `profile.save()` after updating count and flag | Ticket 3, `test_banned_word_..._counts_violation` |
| 4 | `services.moderate` | `> FLAG_AFTER_VIOLATIONS`, so a user is flagged on the 4th strike, not the 3rd | `>=` | Ticket 3, `test_user_is_flagged_after_three_violations` |
| 5 | `services.moderate` | the `is_flagged` check is **inside** `if words:`, so flagged users can still post clean reviews | move the check to before the content check | not reported, `test_flagged_user_is_blocked_...` |
| 6 | `services.update_review` | moderates `review.body` (the **old** text) | `moderate(user, data.get("body", review.body))` | not reported, `test_editing_a_review_runs_moderation_...` |
| 7 | `content_checker.py` | `re.findall(r"[a-z]+", text)` without `.lower()`, so `TRASH` is never even tokenized | `text.lower()` | hidden `test_banned_words_match_regardless_of_case` |
| 8 | `content_checker.py` | returns words in found order, with duplicates (docstring says sorted, unique) | `sorted({...})` | hidden `test_violated_words_are_unique_and_sorted` |
| 9 | `views.py` `ReviewDetailView.patch` | no author check: anyone can edit anyone's review | `if review.author_id != request.user.id: raise PermissionDenied("You can only edit your own reviews.")` | hidden `test_cannot_edit_someone_elses_review` |
| 10 | `services.create_review` | no duplicate check, so the DB unique constraint raises `IntegrityError` (500) | check `.exists()` first and raise a 409 `APIException` | hidden `test_second_review_of_same_movie_returns_409` |

Hidden regression guards (pass on the buggy code and must keep passing):
`test_clean_edit_by_author_is_saved`, `test_list_without_search_returns_all_movies_sorted`.

## Things to notice

- **One root cause, many symptoms:** bug 2 turns 4 of the 6 tests into `400`.
  Print the 400's body once and the cause is obvious.
- **The same test can need two fixes:** the "flag after 3" test needs bug 3
  (save) *and* bug 4 (`>=`). Its failure message changes from `0 != 3` to
  `False is not true` in between. That's progress.
- **Where a check sits matters as much as what it says:** bugs 5 and 6 have
  correct code in the wrong place, or applied to the wrong value.
- **Read the docstring:** bugs 7 and 8 contradict the checker's own
  documentation.
