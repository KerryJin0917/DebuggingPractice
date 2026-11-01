"""The six acceptance tests for the review & moderation API. Don't change them."""
from django.contrib.auth import get_user_model
from django.test import TestCase

from reviews.models import Movie, Review, ReviewerProfile, Violation


class ReviewApiTests(TestCase):
    def setUp(self):
        self.alice = get_user_model().objects.create(username="alice")
        self.dark_knight = Movie.objects.create(title="The Dark Knight", release_year=2008)
        self.dark_city = Movie.objects.create(title="Dark City", release_year=1998)
        self.arrival = Movie.objects.create(title="Arrival", release_year=2016)

    # helpers -------------------------------------------------------------
    def headers(self, user=None):
        return {"HTTP_X_USER_ID": str((user or self.alice).pk)}

    def post_review(self, movie, body, rating=8, user=None):
        return self.client.post(
            f"/api/movies/{movie.pk}/reviews/",
            {"rating": rating, "body": body},
            content_type="application/json",
            **self.headers(user),
        )

    def profile(self, user=None):
        return ReviewerProfile.objects.get_or_create(user=user or self.alice)[0]

    # tests ---------------------------------------------------------------
    def test_search_movies_by_partial_title_case_insensitive(self):
        response = self.client.get("/api/movies/", {"search": "DARK"}, **self.headers())

        self.assertEqual(response.status_code, 200)
        self.assertEqual([m["title"] for m in response.json()], ["Dark City", "The Dark Knight"])

    def test_create_clean_review_returns_201(self):
        response = self.post_review(self.arrival, "Beautiful and moving.", rating=9)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["rating"], 9)
        self.assertEqual(response.json()["author"], "alice")
        self.assertTrue(Review.objects.filter(movie=self.arrival, author=self.alice, rating=9).exists())

    def test_banned_word_returns_403_and_counts_violation(self):
        response = self.post_review(self.arrival, "Total trash from start to finish.")

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.json(),
            {"detail": "Review contains inappropriate language.", "violated_words": ["trash"]},
        )
        self.assertFalse(Review.objects.exists())
        self.assertEqual(self.profile().violation_count, 1)
        self.assertEqual(Violation.objects.get(user=self.alice).words, "trash")

    def test_user_is_flagged_after_three_violations(self):
        for movie in (self.dark_knight, self.dark_city, self.arrival):
            self.assertEqual(self.post_review(movie, "What a scam.").status_code, 403)

        profile = self.profile()
        self.assertEqual(profile.violation_count, 3)
        self.assertTrue(profile.is_flagged)

    def test_flagged_user_is_blocked_even_for_clean_reviews(self):
        ReviewerProfile.objects.create(user=self.alice, violation_count=3, is_flagged=True)

        response = self.post_review(self.arrival, "A thoughtful, clean review.")

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), {"detail": "Your account is flagged."})
        self.assertFalse(Review.objects.exists())
        self.assertEqual(self.profile().violation_count, 3)

    def test_editing_a_review_runs_moderation_on_the_new_text(self):
        review = Review.objects.create(movie=self.arrival, author=self.alice, rating=9, body="Loved it.")

        response = self.client.patch(
            f"/api/reviews/{review.pk}/",
            {"body": "Actually it was garbage."},
            content_type="application/json",
            **self.headers(),
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["violated_words"], ["garbage"])
        review.refresh_from_db()
        self.assertEqual(review.body, "Loved it.")
        self.assertEqual(self.profile().violation_count, 1)
