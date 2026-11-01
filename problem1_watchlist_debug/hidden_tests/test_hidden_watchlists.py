"""HIDDEN TESTS: the grader's extra checks. Don't open until you're done.

Each one maps to a bug the prompt does not mention, or to a regression guard
for behavior that should keep working after your fixes. Run with:

    python manage.py test hidden_tests
"""
from django.contrib.auth import get_user_model
from django.test import TestCase

from movies.models import Movie, WatchList, WatchListEntry


def _auth(user):
    return {"HTTP_X_USER_ID": str(user.pk)}


class HiddenWatchListTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.alice = User.objects.create(username="alice")
        self.bob = User.objects.create(username="bob")
        self.movie = Movie.objects.create(title="Arrival", genre="Sci-Fi", release_year=2016)
        self.other_movie = Movie.objects.create(title="Heat", genre="Crime", release_year=1995)
        self.watchlist = WatchList.objects.create(owner=self.alice, name="Weekend")

    def test_update_watchlist_name_persists(self):
        response = self.client.patch(
            f"/api/watchlists/{self.watchlist.pk}/",
            {"name": "Rainy day"},
            content_type="application/json",
            **_auth(self.alice),
        )
        self.assertEqual(response.status_code, 200)
        self.watchlist.refresh_from_db()
        self.assertEqual(self.watchlist.name, "Rainy day")

    def test_delete_watchlist_returns_204(self):
        response = self.client.delete(f"/api/watchlists/{self.watchlist.pk}/", **_auth(self.alice))
        self.assertEqual(response.status_code, 204)
        self.assertFalse(WatchList.objects.filter(pk=self.watchlist.pk).exists())

    def test_cannot_read_or_delete_another_users_watchlist(self):
        url = f"/api/watchlists/{self.watchlist.pk}/"
        self.assertEqual(self.client.get(url, **_auth(self.bob)).status_code, 404)
        self.assertEqual(self.client.delete(url, **_auth(self.bob)).status_code, 404)
        add = self.client.post(
            f"{url}movies/", {"movie_id": self.movie.pk}, content_type="application/json", **_auth(self.bob)
        )
        self.assertEqual(add.status_code, 404)
        self.assertTrue(WatchList.objects.filter(pk=self.watchlist.pk).exists())
        self.assertEqual(WatchListEntry.objects.count(), 0)

    def test_unauthenticated_request_returns_401(self):
        response = self.client.get("/api/watchlists/")
        self.assertEqual(response.status_code, 401)

    def test_blank_name_is_rejected(self):
        response = self.client.post(
            "/api/watchlists/", {"name": "   "}, content_type="application/json", **_auth(self.alice)
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("name", response.json())
        self.assertEqual(WatchList.objects.filter(owner=self.alice).count(), 1)

    def test_add_unknown_movie_returns_404(self):
        response = self.client.post(
            f"/api/watchlists/{self.watchlist.pk}/movies/",
            {"movie_id": 424242},
            content_type="application/json",
            **_auth(self.alice),
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "Movie not found.")

    def test_bulk_with_unknown_movie_applies_nothing(self):
        response = self.client.post(
            f"/api/watchlists/{self.watchlist.pk}/movies/bulk/",
            {"add": [self.movie.pk, self.other_movie.pk, 424242]},
            content_type="application/json",
            **_auth(self.alice),
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(WatchListEntry.objects.count(), 0)
