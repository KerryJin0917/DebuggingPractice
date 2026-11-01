"""The six acceptance tests for the watch-list API.

Do not change the assertions. Fixing the helpers in factories.py is allowed.
"""
from django.test import TestCase

from movies.models import WatchList, WatchListEntry

from .factories import auth, make_movie, make_user, make_watchlist


class WatchListApiTests(TestCase):
    def setUp(self):
        self.user = make_user("alice")
        self.inception = make_movie("Inception", "Sci-Fi", 2010)
        self.arrival = make_movie("Arrival", "Sci-Fi", 2016)
        self.parasite = make_movie("Parasite", "Thriller", 2019)

    def post(self, url, data):
        return self.client.post(url, data, content_type="application/json", **auth(self.user))

    def test_create_watchlist_returns_201_and_persists(self):
        response = self.post("/api/watchlists/", {"name": "Date night", "description": "Cozy picks"})

        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertEqual(body["name"], "Date night")
        self.assertEqual(body["movie_count"], 0)
        self.assertTrue(
            WatchList.objects.filter(pk=body["id"], owner=self.user, name="Date night").exists()
        )

        listing = self.client.get("/api/watchlists/", **auth(self.user)).json()
        self.assertEqual([w["name"] for w in listing], ["Date night"])

    def test_add_movie_to_watchlist_persists(self):
        watchlist = make_watchlist(self.user)

        response = self.post(f"/api/watchlists/{watchlist.pk}/movies/", {"movie_id": self.arrival.pk})

        self.assertEqual(response.status_code, 201)
        self.assertEqual([m["title"] for m in response.json()["movies"]], ["Arrival"])
        self.assertTrue(
            WatchListEntry.objects.filter(watchlist=watchlist, movie=self.arrival).exists()
        )

    def test_add_movie_to_missing_watchlist_returns_404(self):
        response = self.post("/api/watchlists/9999/movies/", {"movie_id": self.inception.pk})

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "Watch list not found.")
        self.assertEqual(WatchListEntry.objects.count(), 0)

    def test_add_duplicate_movie_returns_409(self):
        watchlist = make_watchlist(self.user)
        url = f"/api/watchlists/{watchlist.pk}/movies/"

        first = self.post(url, {"movie_id": self.arrival.pk})
        second = self.post(url, {"movie_id": self.arrival.pk})

        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 409)
        self.assertEqual(second.json()["detail"], "Movie is already in this watch list.")
        self.assertEqual(WatchListEntry.objects.filter(watchlist=watchlist).count(), 1)

    def test_remove_movie_from_watchlist(self):
        watchlist = make_watchlist(self.user)
        WatchListEntry.objects.create(watchlist=watchlist, movie=self.inception)
        WatchListEntry.objects.create(watchlist=watchlist, movie=self.parasite)

        response = self.client.delete(
            f"/api/watchlists/{watchlist.pk}/movies/{self.inception.pk}/", **auth(self.user)
        )

        self.assertEqual(response.status_code, 204)
        remaining = WatchListEntry.objects.filter(watchlist=watchlist).values_list("movie__title", flat=True)
        self.assertEqual(list(remaining), ["Parasite"])

    def test_bulk_add_then_remove(self):
        watchlist = make_watchlist(self.user)
        url = f"/api/watchlists/{watchlist.pk}/movies/bulk/"
        all_ids = [self.inception.pk, self.arrival.pk, self.parasite.pk]

        added = self.post(url, {"add": all_ids})
        self.assertEqual(added.status_code, 200)
        self.assertEqual(added.json()["movie_count"], 3)

        removed = self.post(url, {"remove": [self.arrival.pk]})
        self.assertEqual(removed.status_code, 200)
        self.assertEqual(
            sorted(m["title"] for m in removed.json()["movies"]), ["Inception", "Parasite"]
        )
        self.assertEqual(WatchListEntry.objects.filter(watchlist=watchlist).count(), 2)
