# 05: The debugging loop, step by step (with commands and the debugger)

This is the hands-on version of `01_method.md`: exactly what to type and
what to look for, one step at a time.

- **Part A** (no spoilers) is the basic loop. Use it on any problem.
- **Part B** (⚠️ spoilers for Problem 3) runs the loop on
  `problem3_reviews_moderation_debug/`, using a different locating tool for
  each bug. All output in Part B is from real runs.

---

# Part A: The basic loop

```
 Step 1  Run everything            → get the list of failures
 Step 2  Write the failure list    → pick the next one
 Step 3  Run that one test         → fast feedback (1 second)
 Step 4  Read the failure          → what was expected vs what happened
 Step 5  Locate                    → which file/function
 Step 6  Isolate (debugger/prints) → which line, and why
 Step 7  Patch                     → smallest change
 Step 8  Verify                    → that test, then everything, then git diff
         ↺ back to Step 2
```

## Step 0: Set up (once)

```bash
cd DebuggingPractice
python -m venv .venv
source .venv/bin/activate                  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cd problem3_reviews_moderation_debug       # always run commands from the problem folder
python manage.py check                     # should print: System check identified no issues
```

Before you start, check that you can get back to a clean state:

```bash
git status                                 # nothing modified yet
git diff                                   # empty
```

To undo all your changes later: `git checkout -- .`

## Step 1: Run the whole suite

```bash
python manage.py test tests 2>&1 | tee /tmp/before.txt
```

`tee` shows the output and saves it, so you can compare later. Look at
three things first:

1. The last line: `OK`, or `FAILED (failures=N, errors=M)`.
2. `Ran N tests`: if N is smaller than expected (e.g. `Ran 1 test` when
   there are 6), a test file failed to import. Fix that first.
3. The header of each failure: `FAIL: test_name (...)` or `ERROR: test_name (...)`.

**FAIL vs ERROR:**

| | Meaning | Where the bug usually is |
|---|---|---|
| `FAIL` | an `assert...` didn't hold, so the code ran but returned the wrong thing | logic, status codes, missing save |
| `ERROR` | an exception was raised (crash, 500, import error) | the traceback points at it |

To see just the summary lines:

```bash
python manage.py test tests 2>&1 | grep -E "^(FAIL|ERROR):|Error:"
```

## Step 2: Write the failure list

Keep a scratch file (or paper) with one line per failing test:

```
[ ] test_create_clean_review_returns_201   400 != 201
[ ] test_banned_word_...                    400 != 403
...
```

**Look for repeated symptoms.** If four tests all say `400 != ...`, they
probably share **one** root cause. Pick one of them first. Otherwise pick the
**simplest-looking** failure first.

## Step 3: Run just one test

```bash
# full label: module.Class.method
python manage.py test tests.test_reviews.ReviewApiTests.test_create_clean_review_returns_201

# or by name pattern (-k is a substring match; repeat -k to OR several)
python manage.py test tests -k create_clean
python manage.py test tests -k search -k flagged
```

A single test runs in about a second, so you can iterate fast.

## Step 4: Read the failure

```
FAIL: test_create_clean_review_returns_201 (tests.test_reviews.ReviewApiTests...)
Traceback (most recent call last):
  File ".../tests/test_reviews.py", line 40, in test_create_clean_review_returns_201
    self.assertEqual(response.status_code, 201)
AssertionError: 400 != 201
```

- `assertEqual(actual, expected)` prints **`actual != expected`**: the code
  returned **400**, and the test wanted **201**.
- Open the test at that line (`tests/test_reviews.py:40`) and read the
  **whole test**: what request does it send, and what does it check after the
  failing line?
- Write one sentence: *"Posting a clean review with rating 9 should give 201,
  but gives 400."*

For an **ERROR**, read the traceback **bottom-up**. The last line is the
exception. Go up until you reach the **first file in the project** (skip
`site-packages/django/...` and `rest_framework/...`). That frame is your
starting point.

## Step 5: Locate

Follow the request through the code:

```
test sends   POST /api/movies/4/reviews/
urls.py      path("movies/<int:movie_id>/reviews/", views.MovieReviewsView...)
views.py     MovieReviewsView.post  → serializer → services.create_review
services.py  create_review → moderate → content_checker
```

Commands that help:

```bash
grep -n "reviews/" reviews/urls.py                 # which view handles the URL?
grep -n "def post\|def patch" reviews/views.py      # find the handler
grep -rn "max_value\|min_value" reviews/           # find validation rules
grep -rn "status=" reviews/views.py                # find every status code returned
grep -rn "save()\|\.create(" reviews/              # find every DB write
```

A **400** usually comes from serializer validation. A **403 or 404** comes
from an explicit `raise` or `get_object_or_404`. A **500** gives you a
traceback.

## Step 6: Isolate the exact line

Pick the lightest tool that answers your question.

### 6a. Inspect the failing test's state with `--pdb`

```bash
python manage.py test tests -k create_clean --pdb
```

When the assertion fails, you get a `(Pdb)` prompt **inside the test**, with
all its variables available:

```
(Pdb) p response.status_code
(Pdb) p response.json()          # the error body usually names the problem
(Pdb) q                          # quit
```

This is the best first move for any wrong status code: the response body
often tells you exactly what went wrong.

### 6b. Pause inside the app code with `breakpoint()`

Add a line in the suspect function:

```python
def get(self, request):
    breakpoint()                       # TEMPORARY
    query = request.query_params.get("q")
```

Then run the single test, **without** `--pdb`:

```bash
python manage.py test tests -k search
```

It stops at that line. Useful commands:

| Command | Does |
|---|---|
| `l` / `ll` | show code around the current line / the whole function |
| `n` | run the current line and stop at the next one (**n**ext) |
| `s` | **s**tep *into* the function called on this line |
| `r` | run until the current function **r**eturns |
| `c` | **c**ontinue until the next breakpoint (or the end) |
| `p expr` / `pp expr` | print / pretty-print any expression, e.g. `p request.data` |
| `args` | show the current function's arguments |
| `w` | **w**here am I? (call stack) |
| `u` / `d` | move **u**p/**d**own the stack to look at the caller's variables |
| `b file.py:LINE` | set another breakpoint |
| `q` | quit |

⚠️ When you stop at `breakpoint()`, the line **after** it hasn't run yet.
Press `n` once to move onto that line and again to run it.

### 6c. Print debugging

Sometimes a single print line is faster than stepping:

```python
print("DEBUG moderate:", repr(text), "flagged=", profile.is_flagged, "words=", words)
```

```bash
python manage.py test tests -k flagged 2>&1 | grep DEBUG
```

Prefix your prints with `DEBUG` so they're easy to grep for and to remove.

### 6d. Call one function directly

If the suspect is a pure function, test it on its own:

```bash
python -c "from reviews.content_checker import find_banned_words as f; print(f('This is TRASH!'))"
```

For anything that touches the database, use the Django shell. It uses
`db.sqlite3`, so run `migrate` and `seed_demo` first:

```bash
python manage.py shell -c "from reviews.models import *; print(ReviewerProfile.objects.values())"
```

### 6e. Reproduce by hand (like the OA's browser UI)

```bash
python manage.py migrate && python manage.py seed_demo
python manage.py runserver
```

In a second terminal:

```bash
curl -s -H "X-User-Id: 1" "localhost:8000/api/movies/?search=dark"
curl -s -X POST -H "X-User-Id: 1" -H "Content-Type: application/json" \
     -d '{"rating": 9, "body": "Beautiful."}' localhost:8000/api/movies/4/reviews/
curl -s -H "X-User-Id: 1" localhost:8000/api/me/moderation/
curl -s -i localhost:8000/api/me/moderation/ | head -1     # -i shows the status line
```

### Is it isolated?

Before you edit, you should be able to finish this sentence: **"Line N does
X, but the contract says Y."** If you can't, keep isolating.

### (Optional) IDE debugger

In VS Code, add this to `.vscode/launch.json`, set a red-dot breakpoint, and
press F5:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Django tests (problem 3)",
      "type": "debugpy",
      "request": "launch",
      "program": "${workspaceFolder}/problem3_reviews_moderation_debug/manage.py",
      "args": ["test", "tests", "-k", "create_clean"],
      "cwd": "${workspaceFolder}/problem3_reviews_moderation_debug",
      "django": true,
      "justMyCode": true
    }
  ]
}
```

## Step 7: Patch

- Change the **smallest** thing that makes the line match the contract.
- Don't touch test assertions.
- **Remove** your `breakpoint()` and `DEBUG` prints now, not later.

## Step 8: Verify

```bash
python manage.py test tests -k <the test>        # 1. that test passes
python manage.py test tests                      # 2. nothing else broke; maybe more now pass
git diff                                         # 3. only the lines you meant to change
grep -rn "breakpoint()\|DEBUG" reviews/          # 4. no leftovers (should print nothing)
```

If the **message** of another failing test changed, look at it again: your
fix may have uncovered the next bug on the same path. Then go back to
**Step 2**.

## After 6/6: hunting for hidden bugs

1. Re-read the contract line by line. For each rule, ask: *which line
   implements this? Is it tested?*
2. For untested rules, write a short throwaway test in `tests/test_probe.py`
   (see `02_problem1_debugging_walkthrough.md` for an example) and run it.
3. Read docstrings and compare them with the code. A docstring that
   promises something the code doesn't do is a hidden test waiting to fail.
4. Delete `tests/test_probe.py` when you're done.

## One-page checklist

```
□ run all → note Ran N and FAIL/ERROR list
□ group repeated symptoms → pick one
□ run one test (-k)
□ read: actual != expected; read the whole test
□ locate: url → view → serializer → service
□ isolate: --pdb (p response.json()) / breakpoint() / DEBUG print / python -c / curl
□ say "line N does X but contract says Y"
□ smallest patch; remove debug code
□ re-run one → re-run all → git diff → grep leftovers
□ repeat; at 6/6 audit the contract and docstrings for hidden bugs
```

---

# Part B: Worked example (Problem 3, ⚠️ spoilers)

All commands run from `problem3_reviews_moderation_debug/`.

## Step 1: Run everything

```bash
python manage.py test tests 2>&1 | grep -E "^(FAIL|ERROR):|Error:"
```

```
FAIL: test_banned_word_returns_403_and_counts_violation
AssertionError: 400 != 403
FAIL: test_create_clean_review_returns_201
AssertionError: 400 != 201
FAIL: test_editing_a_review_runs_moderation_on_the_new_text
AssertionError: 200 != 403
FAIL: test_flagged_user_is_blocked_even_for_clean_reviews
AssertionError: 400 != 403
FAIL: test_search_movies_by_partial_title_case_insensitive
AssertionError: Lists differ: ['Arrival', 'Dark City', 'The Dark Knight'] != ['Dark City', 'The Dark Knight']
FAIL: test_user_is_flagged_after_three_violations
AssertionError: 400 != 403
```

## Step 2: Failure list

```
[ ] create_clean          400 != 201   ┐
[ ] banned_word           400 != 403   │ four tests get 400:
[ ] three_violations      400 != 403   │ probably ONE shared cause. Start here.
[ ] flagged_user          400 != 403   ┘
[ ] search                all movies returned
[ ] editing               200 != 403
```

## Round 1: the 400s → tool: `--pdb` + `p response.json()`

```bash
python manage.py test tests -k create_clean --pdb
```

```
Opening PDB: AssertionError('400 != 201')
> .../tests/test_reviews.py(40)test_create_clean_review_returns_201()
-> self.assertEqual(response.status_code, 201)
(Pdb) p response.status_code
400
(Pdb) p response.json()
{'rating': ['Ensure this value is less than or equal to 5.']}
(Pdb) q
```

- **Locate:** `grep -rn "max_value" reviews/` finds `reviews/serializers.py:25`.
- **Isolate:** "Line 25 caps rating at 5, but the contract says 1–10." The
  tests post ratings 8 and 9.
- **Patch:** `max_value=5` → `max_value=10`.
- **Verify:** re-run everything:

```
FAIL: test_banned_word_returns_403_and_counts_violation
AssertionError: 0 != 1
FAIL: test_editing_a_review_runs_moderation_on_the_new_text
AssertionError: 200 != 403
FAIL: test_flagged_user_is_blocked_even_for_clean_reviews
AssertionError: 201 != 403
FAIL: test_search_movies_by_partial_title_case_insensitive
AssertionError: Lists differ: [...]
FAIL: test_user_is_flagged_after_three_violations
AssertionError: 0 != 3
```

`create_clean` passes, and three other tests now fail with **different
messages**. Those are new, real bugs that the 400 was hiding. Update the list.

## Round 2: search → tool: `breakpoint()` in the view

The test asks for `?search=DARK` and gets every movie. So is the filter
running at all? Add `breakpoint()` above `reviews/views.py:14` and run:

```bash
python manage.py test tests -k search
```

```
> .../reviews/views.py(14)get()
-> breakpoint()
(Pdb) p request.query_params
<QueryDict: {'search': ['DARK']}>
(Pdb) n
> .../reviews/views.py(15)get()
-> query = request.query_params.get("q")
(Pdb) n
> .../reviews/views.py(16)get()
-> if query:
(Pdb) p query
None
(Pdb) c
```

- **Isolate:** "The request sends `search`, but line 15 reads `q`, so
  `query` is `None` and the filter is skipped."
- **Patch:** remove `breakpoint()`, then change `.get("q")` to `.get("search")`.
- **Verify:** `python manage.py test tests -k search` gives `OK`.

## Round 3: violation not counted (`0 != 1`) → tool: `breakpoint()` + comparing memory vs DB

The response was a correct 403, but `violation_count` is 0 afterward. Was it
never incremented, or incremented and never saved? Pause just before the
`raise` in `services.moderate`:

```python
        if profile.violation_count > FLAG_AFTER_VIOLATIONS:
            profile.is_flagged = True
        breakpoint()                      # TEMPORARY
        raise ContentBlocked(words)
```

```bash
python manage.py test tests -k banned_word
```

```
> .../reviews/services.py(37)moderate()
-> breakpoint()
(Pdb) p words
['trash']
(Pdb) p profile.violation_count
1
(Pdb) p ReviewerProfile.objects.get(user=user).violation_count
0
(Pdb) c
```

- **Isolate:** "In memory it's 1, in the database it's 0, so the profile is
  never saved."
- **Patch:** remove `breakpoint()` and add `profile.save()` **after** the
  flag update and before `raise` (so both changes are saved).
- **Verify:** `-k banned_word` gives `OK`. Then run everything:

```
FAIL: test_editing_a_review_runs_moderation_on_the_new_text
AssertionError: 200 != 403
FAIL: test_flagged_user_is_blocked_even_for_clean_reviews
AssertionError: 201 != 403
FAIL: test_user_is_flagged_after_three_violations
AssertionError: False is not true
```

`three_violations` changed from `0 != 3` to `False is not true`. Same test,
next bug.

## Round 4: not flagged at 3 → tool: `--pdb` on the assertion

```bash
python manage.py test tests -k three_violations --pdb
```

```
Opening PDB: AssertionError('False is not true')
> .../tests/test_reviews.py(63)test_user_is_flagged_after_three_violations()
-> self.assertTrue(profile.is_flagged)
(Pdb) p profile.violation_count
3
(Pdb) p profile.is_flagged
False
(Pdb) q
```

- **Isolate:** count is 3, but not flagged. The flag line is
  `if profile.violation_count > FLAG_AFTER_VIOLATIONS:`, and `3 > 3` is
  False. The contract says flag when it **reaches** 3.
- **Patch:** `>` → `>=`.
- **Verify:** `-k three_violations` gives `OK`.

## Round 5: flagged user can post a clean review → tool: DEBUG print

The question: *what does `moderate` see for this request?* Add one print
right after `words = find_banned_words(text)`:

```python
    print("DEBUG moderate:", repr(text), "flagged=", profile.is_flagged, "words=", words)
```

```bash
python manage.py test tests -k flagged_user 2>&1 | grep -E "DEBUG|Error:"
```

```
DEBUG moderate: 'A thoughtful, clean review.' flagged= True words= []
AssertionError: 201 != 403
```

- **Isolate:** `flagged=True`, but `words=[]`, and the `is_flagged` check is
  nested **inside** `if words:`, so it never runs for clean text. The
  contract says a flagged user can't post *anything*.
- **Patch:** remove the print and move the flagged check up, before the
  content check:

```python
def moderate(user, text):
    profile = get_profile(user)
    if profile.is_flagged:
        raise PermissionDenied("Your account is flagged.")
    words = find_banned_words(text)
    if words:
        profile.violation_count += 1
        ...
```

- **Verify:** `-k flagged_user` gives `OK`, then run everything. One left.

## Round 6: edit isn't moderated → tool: `breakpoint()` + `s` (step into)

The PATCH with a banned word returns 200. Add `breakpoint()` above
`moderate(user, review.body)` in `services.update_review`, then step
**into** `moderate` to see what text it gets:

```bash
python manage.py test tests -k editing
```

```
> .../reviews/services.py(47)update_review()
-> breakpoint()
(Pdb) p data
{'body': 'Actually it was garbage.'}
(Pdb) n
> .../reviews/services.py(48)update_review()
-> moderate(user, review.body)
(Pdb) s
--Call--
> .../reviews/services.py(26)moderate()
-> def moderate(user, text):
(Pdb) args
user = <User: alice>
text = 'Loved it.'
(Pdb) c
```

- **Isolate:** "`moderate` gets the **old** body (`review.body`), not the
  new one in `data`."
- **Patch:** remove `breakpoint()`, then
  `moderate(user, data.get("body", review.body))`. Keep it **before** the
  `setattr`/`save()`, so a blocked edit leaves the review unchanged.
- **Verify:**

```bash
python manage.py test tests
```

```
Ran 6 tests
OK
```

```bash
git diff --stat
grep -rn "breakpoint()\|DEBUG" reviews/          # prints nothing
```

**6/6.** Six rounds, five different tools.

## Round 7: hidden bugs → tools: contract and docstring audit, `python -c`

Read the contract again for rules no visible test covers:

| Rule | Covered? | Check |
|---|---|---|
| Matching is case-insensitive; result sorted, no duplicates | no | call the checker directly |
| Only the author can edit (403 message) | no | look at `ReviewDetailView.patch`: no author check at all |
| Second review of the same movie → 409 | no | `create_review` has no check; the DB has a unique constraint, so it'll be a 500 |

Call the checker directly:

```bash
python -c "from reviews.content_checker import find_banned_words as f; print(f('This is TRASH! Pure Garbage.')); print(f('trash, scam, and more trash'))"
```

```
[]
['trash', 'scam', 'trash']
```

Both results contradict the function's own docstring ("case-insensitive",
"sorted and has no duplicates"). The regex `[a-z]+` never matches capital
letters, and the list comprehension keeps order and duplicates.

Patches:

```python
# content_checker.py
    words = re.findall(r"[a-z]+", text.lower())
    return sorted({word for word in words if word in BANNED_WORDS})
```

```python
# views.py: ReviewDetailView.patch, right after get_object_or_404
        if review.author_id != request.user.id:
            raise PermissionDenied("You can only edit your own reviews.")
```

```python
# services.py
class Conflict(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_code = "conflict"

def create_review(user, movie, data):
    if Review.objects.filter(movie=movie, author=user).exists():
        raise Conflict("You have already reviewed this movie.")
    moderate(user, data["body"])
    ...
```

(`PermissionDenied` comes from `rest_framework.exceptions`.)

```bash
python -c "from reviews.content_checker import find_banned_words as f; print(f('This is TRASH! Pure Garbage.')); print(f('trash, scam, and more trash'))"
```

```
['garbage', 'trash']
['scam', 'trash']
```

```bash
python manage.py test tests hidden_tests
```

```
Ran 12 tests
OK
```

## Which tool for which symptom?

| Symptom | Fastest tool | Used in |
|---|---|---|
| Wrong status code (esp. 400) | `--pdb`, then `p response.json()` | Round 1 |
| "Input seems ignored" | `breakpoint()` at the top of the view, `p request.query_params` / `p request.data` | Round 2 |
| "Response OK but DB wrong" | `breakpoint()` before return; compare the object with `Model.objects.get(...)` | Round 3 |
| Wrong final state | `--pdb` and inspect the objects the test loaded | Round 4 |
| "Branch never runs" | one `DEBUG` print of the condition's inputs | Round 5 |
| "Function got the wrong argument" | `breakpoint()` + `s` + `args` | Round 6 |
| Pure helper function | `python -c "..."` | Round 7 |
