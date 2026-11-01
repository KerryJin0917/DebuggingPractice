"""Shared helpers for the watch-list tests."""
from django.contrib.auth import get_user_model

from movies.models import Movie, WatchList


def make_user(username="alice"):
    return get_user_model().objects.create(username=username)


def make_movie(title="Inception", genre=DEFAULT_GENRE, release_year=2010):
    return Movie.objects.create(title=title, genre=genre, release_year=release_year)


def make_watchlist(owner, name="Weekend", description=""):
    return WatchList.objects.create(owner=owner, name=name, description=description)


def auth(user):
    """Headers that authenticate the test client as ``user``."""
    return {"HTTP_X_USER_ID": str(user.pk)}
