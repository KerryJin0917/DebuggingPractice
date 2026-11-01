# 04: Django / DRF bug patterns cheat sheet

Most OA bugs are one of these shapes. Match the **symptom** in the test
output to a row, then check the listed places first.

## "It said success but nothing changed"

| Bug shape | Example | Where to look |
|---|---|---|
| Object built but never saved | `Entry(watchlist=w, movie=m)` with no `.save()` | services/views around the write |
| Method referenced, not called | `entry.delete` / `obj.save` (no `()`) | grep `\.delete$`, `\.save$` |
| `update_fields` leaves out the column | `save(update_fields=["description"])` after setting `name` | every `save(update_fields=...)` |
| Response serializes the in-memory object | API shows the new value, DB doesn't have it | assert with `refresh_from_db()` |
| Saved to the wrong object or field | `serializer.save()` without `owner=request.user`; writing to `title` instead of `name` | serializer `save()` calls, field names vs the model |
| M2M never linked | `issue = Issue.objects.create(...)` but `issue.tags.add(...)` missing | after `create()` for related data |
| Queryset update result ignored | `qs.filter(...).update()` on the wrong filter, so 0 rows changed | the filter |

## Wrong status code

| Symptom | Likely cause |
|---|---|
| `200 != 201` | create view returns the default status. Use `status=status.HTTP_201_CREATED`. |
| `200 != 204` | delete returns a body. Use `Response(status=status.HTTP_204_NO_CONTENT)`. |
| `403 != 401` | the auth class has no `authenticate_header()`, so DRF falls back to 403 for unauthenticated requests |
| `401/403 != 200` | wrong `permission_classes`, or the test client isn't sending the auth header (`HTTP_X_USER_ID=...` in Django's test client) |
| `500` / exception | `None` not handled (`.first()` returns `None`; use `get_object_or_404`), an uncaught `DoesNotExist`, or an `IntegrityError` from a missing pre-check |
| `400 != 201` | serializer `required=True` on an optional field, wrong field name in the request, `read_only` field expected as input |
| `201 != 400` | missing validation: `allow_blank=True`, `required=False`, no `validate_<field>` |
| `404 != 200` | wrong lookup (`pk=` vs `id=` vs `user_id=`), or a URL pattern that's missing or misordered |
| `200 != 404` | **missing ownership filter** (`filter(pk=pk)` without `owner=request.user`) |

## Wrong data / logic

| Bug shape | Example |
|---|---|
| Inverted comparison | `if exists():` vs `if not exists():`, `==` vs `!=` |
| Boundary | `>` vs `>=`, `< 0` vs `<= 0`, `range(1, n)` vs `range(n)` |
| Wrong variable | `movie_id=watchlist.id` |
| Case or whitespace normalization | `title__contains=q` while stored titles are lowercase. Use `icontains`, or `q.lower()`. |
| Time windows | `now <= created + timedelta(seconds=30)` vs `<`, naive vs aware datetimes (`timezone.now()`) |
| Counter not persisted | `user.violations += 1` with no `user.save()` |
| Order of operations | removes applied before adds, check after write instead of before |
| Ordering | no `order_by`, so results come back in DB order. Tests often expect a stated sort. |
| Float vs rounding | sorting on rounded values; comparing floats with `assertEqual` instead of `assertAlmostEqual` |

## Broken harness (not in the prompt)

| Symptom | Cause |
|---|---|
| `Ran 1 test` + `ImportError: Failed to import test module` | a `NameError` or import error in a test helper, fixture, or `urls.py` |
| `ImproperlyConfigured` / `RuntimeError: Model class ... doesn't declare an explicit app_label` | app missing from `INSTALLED_APPS` |
| `no such table` | migration missing: `python manage.py makemigrations <app>` |
| `NoReverseMatch` | URL name typo in `reverse("...")` |

## Test-runner commands

```bash
python manage.py test tests                                   # visible suite
python manage.py test tests.test_watchlists.WatchListApiTests.test_remove_movie_from_watchlist
python manage.py test tests -k remove -k bulk                 # name patterns (OR)
python manage.py test tests --failfast                        # stop at first failure
python manage.py test tests -v 2                              # list each test
python manage.py test tests -k duplicate --pdb                # debugger at the error
python manage.py test tests -d                                # print SQL on failure
python manage.py test tests --keepdb                          # faster re-runs
```

Inside a test or view while investigating (delete afterward):

```python
print(response.status_code, response.json())    # what did the API actually return?
obj.refresh_from_db()                           # what is really in the DB?
breakpoint()                                    # drop into pdb right here
from django.db import connection; print(connection.queries)  # needs DEBUG=True
```

## DRF quick facts that cause bugs

- `request.data` holds the parsed body (JSON/form). `request.query_params`
  holds the query string. `request.POST` is **empty** for JSON.
- `serializer.is_valid(raise_exception=True)` turns errors into a 400 with a
  `{field: [msgs]}` body.
- `serializer.save(owner=request.user)` passes extra fields into `create()`.
- `ModelSerializer` with `partial=True` is needed for PATCH. Without it,
  required fields missing from the body give a 400.
- `CharField` trims whitespace by default, and `allow_blank=False` is the
  default.
- Raise `NotFound`, `PermissionDenied`, `ValidationError`, or `APIException`
  subclasses from anywhere in the request, and DRF turns them into the right
  status code and a `{"detail": ...}` body.
- `get_object_or_404(Model, pk=..., owner=request.user)` is a one-line
  existence and ownership check.
