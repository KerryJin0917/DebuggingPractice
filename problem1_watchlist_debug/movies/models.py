from django.conf import settings
from django.db import models


class Movie(models.Model):
    title = models.CharField(max_length=200)
    genre = models.CharField(max_length=50)
    release_year = models.PositiveIntegerField()

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return f"{self.title} ({self.release_year})"


class WatchList(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="watchlists"
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, default="")
    movies = models.ManyToManyField(Movie, through="WatchListEntry", related_name="watchlists")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class WatchListEntry(models.Model):
    watchlist = models.ForeignKey(WatchList, on_delete=models.CASCADE, related_name="entries")
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name="entries")
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["watchlist", "movie"], name="unique_movie_per_watchlist"),
        ]
        ordering = ["added_at", "id"]
