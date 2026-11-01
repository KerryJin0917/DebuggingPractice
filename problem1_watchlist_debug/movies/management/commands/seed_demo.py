from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from movies.models import Movie

MOVIES = [
    ("Inception", "Sci-Fi", 2010),
    ("Arrival", "Sci-Fi", 2016),
    ("The Godfather", "Crime", 1972),
    ("Parasite", "Thriller", 2019),
    ("Spirited Away", "Animation", 2001),
    ("Get Out", "Horror", 2017),
]


class Command(BaseCommand):
    help = "Create two demo users and a handful of movies for manual testing."

    def handle(self, *args, **options):
        User = get_user_model()
        for username in ("alice", "bob"):
            user, _ = User.objects.get_or_create(username=username)
            self.stdout.write(f"user {username}: X-User-Id: {user.pk}")
        for title, genre, year in MOVIES:
            movie, _ = Movie.objects.get_or_create(title=title, genre=genre, release_year=year)
            self.stdout.write(f"movie {movie.pk}: {movie}")
