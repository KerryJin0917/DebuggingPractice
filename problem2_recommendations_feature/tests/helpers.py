"""Test helpers for building movies with known average ratings."""
from itertools import count

from django.contrib.auth import get_user_model

from movies.models import Genre, Movie, Rating, WatchedMovie

URL = "/api/ratings/recommendations/user"
_critic_ids = count(1)


def make_user(username):
    return get_user_model().objects.create(username=username)


def make_movie(title, genres=(), critic_scores=(), year=2020):
    """Create a movie and rate it once per score, each by a new critic user.

    ``critic_scores=(7, 8)`` gives the movie an average rating of 7.5.
    """
    movie = Movie.objects.create(title=title, release_year=year)
    movie.genres.set([Genre.objects.get_or_create(name=name)[0] for name in genres])
    for score in critic_scores:
        critic = make_user(f"critic{next(_critic_ids)}")
        Rating.objects.create(user=critic, movie=movie, score=score)
    return movie


def rate(user, movie, score):
    return Rating.objects.create(user=user, movie=movie, score=score)


def watch(user, movie):
    return WatchedMovie.objects.create(user=user, movie=movie)


def auth(user):
    return {"HTTP_X_USER_ID": str(user.pk)}
