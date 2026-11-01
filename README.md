# DebuggingPractice

Practice for the Amazon-style **"AI Assistant Repo Bug-Fix"** OA (Part 2): a
60-minute round with a small Django REST Framework repo, an AI assistant that
only sees one file, 6 visible acceptance tests, and hidden grader tests.

| Folder | Type | Task | Visible / hidden tests |
|---|---|---|---|
| [`problem1_watchlist_debug/`](problem1_watchlist_debug/README.md) | **Debugging only** | Movie watch-list CRUD API. A QA bug list names 3 issues, and more are hidden (including a broken test helper). | 6 / 7 |
| [`problem2_recommendations_feature/`](problem2_recommendations_feature/README.md) | **Feature only** | Build `GET /api/ratings/recommendations/user` ("Recommended For You") from a written spec. | 6 / 10 |
| [`problem3_reviews_moderation_debug/`](problem3_reviews_moderation_debug/README.md) | **Debugging only** (good first problem) | Movie search, reviews, and content moderation (403 on banned words, violation count, flag after 3 strikes). Comes with a step-by-step debugger guide. | 6 / 6 |

## Tutorial

[`tutorial/`](tutorial/README.md) walks through the method (Reproduce → Locate → Isolate →
Patch → Verify), solves both problems step by step with real test output, and
includes a Django/DRF bug-pattern cheat sheet. New to this? Start with
`tutorial/05_debugging_loop_step_by_step.md` Part A (terminal commands, `--pdb`,
`breakpoint()`), and use Problem 3 as your first problem. The walkthroughs are spoilers:
read `tutorial/01_method.md` first and attempt each problem before opening its
walkthrough.

## Setup

```bash
pip install -r requirements.txt
cd problem1_watchlist_debug
python manage.py test tests
```

## How to simulate the OA

1. Start a 60-minute timer and open only the problem's `README.md`.
2. Run `python manage.py test tests` and read the failures before you touch
   any code.
3. Use an AI assistant the way the OA allows: one file at a time. Paste in a
   failing test or traceback and ask it to narrow the bug down to a file, then
   a function, then a line range.
4. When time is up (or you hit 6/6), run `python manage.py test hidden_tests`.
   Those count too.
5. Only then open `SOLUTION/`.

To start over: `git checkout -- <problem folder>`.
