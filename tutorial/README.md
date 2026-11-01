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
| [`05_debugging_loop_step_by_step.md`](05_debugging_loop_step_by_step.md) | **Part A:** the loop as exact steps and terminal commands: running single tests, reading failures, `--pdb`, `breakpoint()` and pdb commands, print debugging, `python -c`, curl, VS Code. **Part B:** solves Problem 3 with a different tool for each bug, using real debugger sessions | Part A: no. Part B: **yes** |
| [`06_problem4_blog_walkthrough.md`](06_problem4_blog_walkthrough.md) | Problem 4 (mock-OA replica): pytest debugging flags, the swallowed-500 trap, 8 bugs in sequence across `views.py`/`utils.py`/`urls.py` with real output at each step, the hidden-suite contract audit, and lessons from the actual mock's AI session | **Yes** |

Suggested order:

1. Read `05_...` **Part A**, then do **Problem 3** with it open next to you.
   Afterward, compare your solve with Part B.
2. Read `01_method.md` and `04_django_drf_bug_patterns.md` (15 min).
3. Attempt Problem 1 for 60 minutes, then read `02_...`.
4. Attempt Problem 2 for 60 minutes, then read `03_...`.
5. Do Problem 4 as a full mock (60 min, 2 visible tests), then read `06_...`.
6. Reset (`git checkout -- problem1_watchlist_debug problem2_recommendations_feature problem3_reviews_moderation_debug problem4_blog_posts_debug`)
   and redo them a few days later. Aim to clear the 6 visible tests in under 30 minutes.

Every output block in these files was copied from a real run of this repo
(paths shortened), so what you see in your terminal should match.
