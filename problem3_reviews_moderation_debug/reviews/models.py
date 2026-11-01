from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Movie(models.Model):
    title = models.CharField(max_length=200)
    release_year = models.PositiveIntegerField()

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title


class Review(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name="reviews")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews")
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)])
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["movie", "author"], name="one_review_per_movie")]
        ordering = ["-created_at", "-id"]


class ReviewerProfile(models.Model):
    """Moderation state for a user. Created on first use (see services.get_profile)."""

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviewer_profile")
    violation_count = models.PositiveIntegerField(default=0)
    is_flagged = models.BooleanField(default=False)


class Violation(models.Model):
    """One rejected review or edit, with the banned words it contained."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="violations")
    text = models.TextField()
    words = models.CharField(max_length=500, help_text="Comma-separated banned words found in text.")
    created_at = models.DateTimeField(auto_now_add=True)
