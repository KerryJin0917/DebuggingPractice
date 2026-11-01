"""HIDDEN TESTS: the grader's extra checks. Don't open until you're done.

    python manage.py test hidden_tests
"""
from django.contrib.auth import get_user_model
from django.test import TestCase

from reviews.models import Movie, Review, ReviewerProfile


class HiddenReviewTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.alice = User.objects.create(username="alice")
        self.bob = User.objects.create(username="bob")
        self.movie = Movie.objects.create(title="Arrival", release_year=2016)
        self.other = Movie.objects.create(title="Heat", release_year=1995)

    def post_review(self, body, user=None, movie=None, rating=7):
        return self.client.post(
            f"/api/movies/{(movie or self.movie).pk}/reviews/",
            {"rating": rating, "body": body},
            content_type="application/json",
            HTTP_X_USER_ID=str((user or self.alice).pk),
        )

    def test_banned_words_match_regardless_of_case(self):
        response = self.post_review("This is TRASH! Pure Garbage.")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["violated_words"], ["garbage", "trash"])

    def test_violated_words_are_unique_and_sorted(self):
        response = self.post_review("trash, scam, and more trash")
        self.assertEqual(response.json()["violated_words"], ["scam", "trash"])
        self.assertEqual(ReviewerProfile.objects.get(user=self.alice).violation_count, 1)

    def test_cannot_edit_someone_elses_review(self):
        review = Review.objects.create(movie=self.movie, author=self.alice, rating=8, body="Great.")
        response = self.client.patch(
            f"/api/reviews/{review.pk}/",
            {"rating": 1},
            content_type="application/json",
            HTTP_X_USER_ID=str(self.bob.pk),
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), {"detail": "You can only edit your own reviews."})
        review.refresh_from_db()
        self.assertEqual(review.rating, 8)

    def test_second_review_of_same_movie_returns_409(self):
        self.assertEqual(self.post_review("First take.").status_code, 201)
        response = self.post_review("Second take.")
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json(), {"detail": "You have already reviewed this movie."})
        self.assertEqual(Review.objects.filter(author=self.alice).count(), 1)

    def test_clean_edit_by_author_is_saved(self):
        review = Review.objects.create(movie=self.movie, author=self.alice, rating=8, body="Great.")
        response = self.client.patch(
            f"/api/reviews/{review.pk}/",
            {"rating": 10, "body": "Even better the second time."},
            content_type="application/json",
            HTTP_X_USER_ID=str(self.alice.pk),
        )
        self.assertEqual(response.status_code, 200)
        review.refresh_from_db()
        self.assertEqual((review.rating, review.body), (10, "Even better the second time."))

    def test_list_without_search_returns_all_movies_sorted(self):
        response = self.client.get("/api/movies/", HTTP_X_USER_ID=str(self.alice.pk))
        self.assertEqual([m["title"] for m in response.json()], ["Arrival", "Heat"])
