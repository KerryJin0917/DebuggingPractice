"""Business logic for watch lists. Views stay thin and call into here."""
from django.db import transaction
from rest_framework import status
from rest_framework.exceptions import APIException, NotFound

from .models import Movie, WatchList, WatchListEntry


class Conflict(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "Conflict."
    default_code = "conflict"


def get_watchlist_for_user(user, watchlist_id):
    """Return the user's watch list with this id, or None if there isn't one."""
    return WatchList.objects.filter(pk=watchlist_id).first()


def get_movie(movie_id):
    try:
        return Movie.objects.get(pk=movie_id)
    except Movie.DoesNotExist:
        raise NotFound("Movie not found.")


def create_watchlist(user, data):
    return WatchList.objects.create(owner=user, **data)


def update_watchlist(watchlist, data):
    for field in ("name", "description"):
        if field in data:
            setattr(watchlist, field, data[field])
    watchlist.save(update_fields=["description", "updated_at"])
    return watchlist


def delete_watchlist(watchlist):
    watchlist.delete()


def add_movie(watchlist, movie_id):
    movie = get_movie(movie_id)
    if WatchListEntry.objects.filter(watchlist=watchlist, movie_id=watchlist.id).exists():
        raise Conflict("Movie is already in this watch list.")
    entry = WatchListEntry(watchlist=watchlist, movie=movie)
    return entry


def remove_movie(watchlist, movie_id):
    entry = WatchListEntry.objects.filter(watchlist=watchlist, movie_id=movie_id).first()
    if entry is None:
        raise NotFound("Movie is not in this watch list.")
    entry.delete


@transaction.atomic
def bulk_update_movies(watchlist, add_ids, remove_ids):
    """Apply every add first, then every remove, all-or-nothing.

    Movies already in the list are skipped on add; movies not in the list are
    skipped on remove. An unknown movie id in ``add_ids`` aborts the whole
    request with 404.
    """
    for i in range(1, len(add_ids)):
        movie_id = add_ids[i]
        if not WatchListEntry.objects.filter(watchlist=watchlist, movie_id=movie_id).exists():
            add_movie(watchlist, movie_id)

    for movie_id in remove_ids:
        WatchListEntry.objects.filter(watchlist=watchlist, movie_id=movie_id).delete()
    return watchlist
