"""The six acceptance tests for GET /api/ratings/recommendations/user."""
from django.test import TestCase

from .helpers import URL, auth, make_movie, make_user, rate, watch


class RecommendationTests(TestCase):
    def setUp(self):
        self.alice = make_user("alice")

    def recommend(self):
        response = self.client.get(URL, **auth(self.alice))
        self.assertEqual(response.status_code, 200, response.content)
        return response.json()

    def titles(self):
        return [movie["title"] for movie in self.recommend()["results"]]

    def test_requires_authentication(self):
        response = self.client.get(URL)
        self.assertEqual(response.status_code, 401)

    def test_excludes_movies_user_watched_or_rated(self):
        watched = make_movie("Watched It", ["Drama"], [8, 8])
        rated = make_movie("Rated It", ["Drama"], [8, 8])
        make_movie("Fresh Pick", ["Drama"], [8, 8])
        watch(self.alice, watched)
        rate(self.alice, rated, 8)

        body = self.recommend()

        self.assertEqual(body["count"], 1)
        self.assertEqual([m["title"] for m in body["results"]], ["Fresh Pick"])

    def test_only_returns_movies_with_average_rating_of_at_least_7(self):
        make_movie("Just Okay", ["Drama"], [6, 7])     # 6.5
        make_movie("Crowd Pleaser", ["Drama"], [8, 8])  # 8.0

        self.assertEqual(self.titles(), ["Crowd Pleaser"])

    def test_high_rating_boosts_similar_genres(self):
        loved = make_movie("Interstellar", ["Sci-Fi"], [9])
        rate(self.alice, loved, 9)
        make_movie("Arrival", ["Sci-Fi"], [7, 8])  # 7.5 * 1.2 = 9.0
        make_movie("Heat", ["Crime"], [8, 8])      # 8.0 * 1.0 = 8.0

        results = self.recommend()["results"]

        self.assertEqual([m["title"] for m in results], ["Arrival", "Heat"])
        self.assertAlmostEqual(results[0]["score"], 9.0, places=3)
        self.assertAlmostEqual(results[1]["score"], 8.0, places=3)

    def test_low_rating_favors_other_genres(self):
        hated = make_movie("Bad Scares", ["Horror"], [3])
        rate(self.alice, hated, 3)
        make_movie("Hereditary", ["Horror"], [8, 8])   # 8.0 * 0.8 = 6.4
        make_movie("Paddington 2", ["Comedy"], [7, 8])  # 7.5 * 1.0 = 7.5

        results = self.recommend()["results"]

        self.assertEqual([m["title"] for m in results], ["Paddington 2", "Hereditary"])
        self.assertAlmostEqual(results[1]["score"], 6.4, places=3)

    def test_watched_but_unrated_movie_boosts_similar_genres(self):
        seen = make_movie("Before Sunrise", ["Romance"], [9])
        watch(self.alice, seen)
        make_movie("La La Land", ["Romance"], [7, 8])     # 7.5 * 1.1 = 8.25
        make_movie("Mad Max", ["Action"], [8, 8])         # 8.0 * 1.0 = 8.0

        results = self.recommend()["results"]

        self.assertEqual([m["title"] for m in results], ["La La Land", "Mad Max"])
        self.assertAlmostEqual(results[0]["score"], 8.25, places=3)
