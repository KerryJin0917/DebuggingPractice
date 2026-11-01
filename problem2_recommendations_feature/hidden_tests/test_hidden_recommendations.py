"""HIDDEN TESTS: the grader's edge cases. Don't open until you're done.

    python manage.py test hidden_tests
"""
from django.test import TestCase

from tests.helpers import URL, auth, make_movie, make_user, rate, watch


class HiddenRecommendationTests(TestCase):
    def setUp(self):
        self.alice = make_user("alice")

    def results(self):
        response = self.client.get(URL, **auth(self.alice))
        self.assertEqual(response.status_code, 200, response.content)
        return response.json()["results"]

    def titles(self):
        return [m["title"] for m in self.results()]

    def test_returns_at_most_10(self):
        for i in range(12):
            make_movie(f"Movie {i:02d}", ["Drama"], [8, 8])
        response = self.client.get(URL, **auth(self.alice)).json()
        self.assertEqual(response["count"], 10)
        self.assertEqual(len(response["results"]), 10)

    def test_response_item_structure_and_rounding(self):
        movie = make_movie("Knives Out", ["Mystery", "Comedy"], [7, 7, 8])  # 7.333...
        [item] = self.results()
        self.assertEqual(set(item), {"id", "title", "genres", "average_rating", "score"})
        self.assertEqual(item["id"], movie.pk)
        self.assertEqual(item["genres"], ["Comedy", "Mystery"])
        self.assertEqual(item["average_rating"], 7.33)
        self.assertEqual(item["score"], 7.333)

    def test_unrated_movies_excluded_and_exactly_7_included(self):
        make_movie("Nobody Rated Me", ["Drama"], [])
        make_movie("Borderline", ["Drama"], [6, 8])  # exactly 7.0
        make_movie("Almost", ["Drama"], [7, 7, 6])   # 6.67
        self.assertEqual(self.titles(), ["Borderline"])

    def test_ties_broken_by_title(self):
        make_movie("Zodiac", ["Thriller"], [8])
        make_movie("Alien", ["Thriller"], [8])
        make_movie("Memento", ["Thriller"], [8])
        self.assertEqual(self.titles(), ["Alien", "Memento", "Zodiac"])

    def test_other_users_history_does_not_exclude(self):
        bob = make_user("bob")
        movie = make_movie("Arrival", ["Sci-Fi"], [8])
        watch(bob, movie)
        rate(bob, movie, 10)  # average becomes 9.0
        [item] = self.results()
        self.assertEqual(item["title"], "Arrival")
        self.assertEqual(item["average_rating"], 9.0)

    def test_boosts_compound_and_multi_genre_movies_use_mean_weight(self):
        for title in ("Interstellar", "Blade Runner"):
            rate(self.alice, make_movie(title, ["Sci-Fi"], [9]), 9)  # Sci-Fi weight 1.44
        make_movie("Dune", ["Sci-Fi", "Drama"], [8])   # 8 * (1.44 + 1.0) / 2 = 9.76
        make_movie("Up", ["Animation"], [9, 10])        # 9.5
        results = self.results()
        self.assertEqual([m["title"] for m in results], ["Dune", "Up"])
        self.assertAlmostEqual(results[0]["score"], 9.76, places=3)

    def test_watched_and_rated_movie_counts_only_as_rated(self):
        seen = make_movie("Interstellar", ["Sci-Fi"], [9])
        watch(self.alice, seen)
        rate(self.alice, seen, 9)
        make_movie("Arrival", ["Sci-Fi"], [7, 8])  # 7.5 * 1.2, not 7.5 * 1.2 * 1.1
        [item] = self.results()
        self.assertAlmostEqual(item["score"], 9.0, places=3)

    def test_rating_of_exactly_5_counts_as_disliked(self):
        rate(self.alice, make_movie("Meh", ["Horror"], [5]), 5)
        make_movie("Hereditary", ["Horror"], [8])  # 6.4
        [item] = self.results()
        self.assertAlmostEqual(item["score"], 6.4, places=3)

    def test_movie_without_genres_uses_neutral_weight(self):
        rate(self.alice, make_movie("Loved", ["Sci-Fi"], [9]), 9)
        make_movie("Genre-less", [], [8])
        [item] = self.results()
        self.assertEqual(item["genres"], [])
        self.assertAlmostEqual(item["score"], 8.0, places=3)

    def test_unknown_user_id_returns_401(self):
        response = self.client.get(URL, HTTP_X_USER_ID="999999")
        self.assertEqual(response.status_code, 401)
