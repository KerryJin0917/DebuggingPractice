# Tutorial

Step-by-step walkthroughs for both practice problems, plus the general method
behind them.

> ⚠️ **Spoilers.** Files 02 and 03 solve the problems. For real practice,
> read `01_method.md` first, try the problem against a timer, and only then
> read its walkthrough.

| File | What it covers | Spoilers? |
|---|---|---|
| [`01_method.md`](01_method.md) | The 5-step loop (Reproduce → Locate → Isolate → Patch → Verify), reading Django tracebacks, test-runner commands, AI prompt templates, the 60-minute time budget | No |
| [`02_problem1_debugging_walkthrough.md`](02_problem1_debugging_walkthrough.md) | Problem 1 (watch-list bugs), bug by bug, with the real test output at each stage, then finding the hidden bugs from the contract | **Yes** |
| [`03_problem2_feature_walkthrough.md`](03_problem2_feature_walkthrough.md) | Problem 2 (recommendations): spec to checklist to staged build, including a "first draft" that passes 6/6 visible tests but fails 3 hidden ones | **Yes** |
| [`04_django_drf_bug_patterns.md`](04_django_drf_bug_patterns.md) | Cheat sheet of Django/DRF bug shapes, what each looks like in a test failure, and where to look | No |

Suggested order:

1. Read `01_method.md` and `04_django_drf_bug_patterns.md` (15 min).
2. Attempt Problem 1 for 60 minutes, then read `02_...`.
3. Attempt Problem 2 for 60 minutes, then read `03_...`.
4. Reset (`git checkout -- problem1_watchlist_debug problem2_recommendations_feature`)
   and redo both a few days later. Aim to clear the 6 visible tests in under 30 minutes.

Every output block in these files was copied from a real run of this repo
(paths shortened), so what you see in your terminal should match.
