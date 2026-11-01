from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from reviews.models import Movie

MOVIES = [
    ("The Dark Knight", 2008),
    ("Dark City", 1998),
    ("Inception", 2010),
    ("Arrival", 2016),
    ("Knives Out", 2019),
    ("Paddington 2", 2017),
]


class Command(BaseCommand):
    help = "Create demo users (alice, bob) and a few movies."

    def handle(self, *args, **options):
        User = get_user_model()
        for username in ("alice", "bob"):
            user, _ = User.objects.get_or_create(username=username)
            self.stdout.write(f"user {username}: X-User-Id: {user.pk}")
        for title, year in MOVIES:
            movie, _ = Movie.objects.get_or_create(title=title, release_year=year)
            self.stdout.write(f"movie {movie.pk}: {title}")
