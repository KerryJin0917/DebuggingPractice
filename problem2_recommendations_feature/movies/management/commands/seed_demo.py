import random

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from movies.models import Genre, Movie, Rating

MOVIES = [
    ("Inception", 2010, ["Sci-Fi", "Action"]),
    ("Arrival", 2016, ["Sci-Fi", "Drama"]),
    ("Interstellar", 2014, ["Sci-Fi", "Drama"]),
    ("Blade Runner 2049", 2017, ["Sci-Fi"]),
    ("The Godfather", 1972, ["Crime", "Drama"]),
    ("Heat", 1995, ["Crime", "Action"]),
    ("Parasite", 2019, ["Thriller", "Drama"]),
    ("Get Out", 2017, ["Horror", "Thriller"]),
    ("Hereditary", 2018, ["Horror"]),
    ("Paddington 2", 2017, ["Comedy", "Family"]),
    ("Spirited Away", 2001, ["Animation", "Family"]),
    ("Mad Max: Fury Road", 2015, ["Action"]),
    ("Knives Out", 2019, ["Comedy", "Crime"]),
    ("La La Land", 2016, ["Romance", "Drama"]),
    ("Before Sunrise", 1995, ["Romance"]),
]


class Command(BaseCommand):
    help = "Create a demo user (alice), five critic users, movies, and critic ratings."

    def handle(self, *args, **options):
        rng = random.Random(7)
        User = get_user_model()
        alice, _ = User.objects.get_or_create(username="alice")
        critics = [User.objects.get_or_create(username=f"critic{i}")[0] for i in range(5)]
        for title, year, genre_names in MOVIES:
            movie, _ = Movie.objects.get_or_create(title=title, release_year=year)
            movie.genres.set([Genre.objects.get_or_create(name=n)[0] for n in genre_names])
            for critic in critics:
                Rating.objects.update_or_create(
                    user=critic, movie=movie, defaults={"score": rng.randint(5, 10)}
                )
            self.stdout.write(f"movie {movie.pk}: {title}")
        self.stdout.write(f"\nLog in as alice with header  X-User-Id: {alice.pk}")
