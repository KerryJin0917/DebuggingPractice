# 01: The method

The OA scores your **engineering loop**, not clever algorithms. The bugs are
shallow: a wrong comparison, a missing `.save()`, a wrong variable. What
costs time is wandering. This loop keeps you from wandering.

```
 ┌─────────────┐   ┌─────────┐   ┌──────────┐   ┌────────┐   ┌──────────┐
 │ 1 Reproduce │──▶│ 2 Locate│──▶│ 3 Isolate│──▶│ 4 Patch│──▶│ 5 Verify │──┐
 └─────────────┘   └─────────┘   └──────────┘   └────────┘   └──────────┘  │
        ▲                                                                   │
        └──────────────────── next failing test ───────────────────────────┘
```

## 0. Orient (first 5 minutes, before touching code)

1. **Read the README and contract once, fully.** Underline every status code,
   error message string, and "must"/"never". Hidden tests come from those
   lines.
2. **Map the layout.** In a Django app a request goes:
   `urls.py → views.py → (serializers.py) → services.py / models.py`.
   Know which file owns which step.
3. **Run the whole suite** and read the summary: `python manage.py test tests`.
4. **Triage the failures** into a quick table:

   | Test | Kind | Guess |
   |---|---|---|
   | `test_x` | `ImportError` / `NameError` | broken harness: fix first |
   | `test_y` | `500` / exception traceback | crash: the traceback tells you where |
   | `test_z` | `AssertionError: 200 != 201` | wrong status code: one-line fix |
   | `test_w` | `AssertionError: [] != ['Arrival']` | "success but nothing changed": missing write |

   Fix order: **harness errors → crashes → cheap one-liners → logic bugs.**
   Cheap wins early protect your score if time runs out.

## 1. Reproduce

Run **only** the failing test so each loop takes about a second:

```bash
python manage.py test tests.test_watchlists.WatchListApiTests.test_remove_movie_from_watchlist
python manage.py test tests -k remove          # every test whose name contains "remove"
python manage.py test tests --failfast         # stop at the first failure
```

Read the assertion: `X != Y` means **actual first, expected second** in
`assertEqual(actual, expected)`. Write down, in one sentence, what the test
expects and what the code did instead.

## 2. Locate

- **If there's a traceback**, read it **bottom-up** and find the **lowest
  frame inside the project** (skip `site-packages/django/...` and
  `rest_framework/...`). That's usually the line to fix, or one line from it.
- **If it's a plain assertion failure** (no traceback into app code), trace
  the request path by hand: URL in the test → `urls.py` → view method →
  service function. Find the line that should have produced the expected
  value.
- Keep a **search shortlist**: `grep -n "status=" movies/views.py`,
  `grep -n "save\|create\|delete" movies/services.py`.

## 3. Isolate

Shrink the suspicious area to **one line and one reason** before editing.

- Re-read the line word by word: is that the right variable, the right
  comparison, the right field name? Is that method actually *called*?
- Need evidence? Drop a temporary `print(...)` or `breakpoint()` in the
  suspect function, or run with `--pdb` to land in the debugger at the
  error:
  ```bash
  python manage.py test tests -k duplicate --pdb
  ```
- `-d` / `--debug-sql` prints the SQL that ran when a test fails. It's handy
  for "nothing was written" bugs: no `INSERT` means no write.
- Ask: **does fixing this explain the whole failure?** If not, there may be
  two bugs on the same path.

## 4. Patch

- **Smallest change that matches the contract.** Don't refactor, rename, or
  "improve" nearby code: every extra line is a new risk and costs review time.
- **Follow the codebase's existing pattern.** If three views call
  `_load_watchlist()` and one doesn't, the fix is to call it, not to invent a
  new `None` check.
- **Never edit test assertions.** Test *helpers or fixtures* can be broken
  and fixable (the prompt usually says so, or the error is clearly in setup).

## 5. Verify

1. Re-run the single test: it should pass now.
2. Re-run the **whole** suite: you may have fixed one test and broken
   another, or **unmasked** a second bug hiding behind the first (common!).
3. Glance at `git diff`. Every changed line should be one you meant to change.

## After the visible tests are green: hunt hidden bugs

Spend leftover time auditing against the **contract**, not the tests:

1. Go through the README's API table **row by row**. For each status code and
   error message, ask: which line produces it? Is there a test for it?
2. For the rows **with no visible test**, write a 3-line throwaway probe test
   (see walkthrough 02 for an example) and run it.
3. Classic hidden-test targets: 401 vs 403, 204 vs 200, ownership checks
   (user A touching user B's data), blank/missing input → 400, boundaries
   (`>` vs `>=`), "is it actually saved?" (`refresh_from_db()`).

## Using the AI assistant (one file at a time)

The OA's assistant only sees the selected file and won't hand you the full
fix. Use it to **narrow things down**, not to write the fix. Templates:

**Localize from a failure** (select the file the traceback points to):
```
This test fails:
<paste the failing test function>
Output:
<paste the assertion or the last ~10 traceback lines>
In the file I have open, which function is most likely responsible?
Give me the line range and the reason, not a rewrite.
```

**Check a hypothesis:**
```
I think line 45 is wrong because it filters on watchlist.id instead of the
movie. Is that consistent with the rest of this function? Is anything else
in this function suspicious?
```

**Spec to code** (feature work, with the service file open):
```
Rule: "<paste one rule from the README>". The models are:
<paste the relevant model fields>.
What Django ORM query expresses this? Just the query, not the whole function.
```

Tips:
- Paste the **contract text**. The assistant can't see the README.
- One question per bug. Long multi-bug prompts get vague answers.
- **Verify every suggestion by running the test.** It's often almost right.

## 60-minute time budget

| Minutes | Debugging problem | Feature problem |
|---|---|---|
| 0–5 | Orient: README, layout, full test run, triage | Orient: README, turn the spec into a numbered checklist, test run |
| 5–40 | Fix loop, cheapest first | Build in stages, running tests after each one |
| 40–52 | Contract audit and probe tests for hidden bugs | Edge-case audit against the checklist |
| 52–60 | Full suite, review the `git diff`, remove debug prints and probe files | Same |

If a single bug eats more than ~8 minutes, **park it**, write down what you
know, and move to the next test. Come back with fresh eyes.
