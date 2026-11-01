from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView

from . import services
from .models import Movie, WatchList
from .serializers import (
    AddMovieSerializer,
    BulkUpdateSerializer,
    MovieSerializer,
    WatchListSerializer,
)


def _load_watchlist(request, watchlist_id):
    watchlist = services.get_watchlist_for_user(request.user, watchlist_id)
    if watchlist is None:
        raise NotFound("Watch list not found.")
    return watchlist


class MovieListView(APIView):
    def get(self, request):
        return Response(MovieSerializer(Movie.objects.all(), many=True).data)


class WatchListListCreateView(APIView):
    def get(self, request):
        watchlists = (
            WatchList.objects.filter(owner=request.user)
            .prefetch_related("movies")
            .order_by("-created_at", "-id")
        )
        return Response(WatchListSerializer(watchlists, many=True).data)

    def post(self, request):
        serializer = WatchListSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        watchlist = services.create_watchlist(request.user, serializer.validated_data)
        return Response(WatchListSerializer(watchlist).data, status=status.HTTP_200_OK)


class WatchListDetailView(APIView):
    def get(self, request, watchlist_id):
        watchlist = _load_watchlist(request, watchlist_id)
        return Response(WatchListSerializer(watchlist).data)

    def patch(self, request, watchlist_id):
        watchlist = _load_watchlist(request, watchlist_id)
        serializer = WatchListSerializer(watchlist, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        services.update_watchlist(watchlist, serializer.validated_data)
        return Response(WatchListSerializer(watchlist).data)

    def delete(self, request, watchlist_id):
        watchlist = _load_watchlist(request, watchlist_id)
        services.delete_watchlist(watchlist)
        return Response({"detail": "Watch list deleted."}, status=status.HTTP_200_OK)


class WatchListMoviesView(APIView):
    def post(self, request, watchlist_id):
        watchlist = services.get_watchlist_for_user(request.user, watchlist_id)
        serializer = AddMovieSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.add_movie(watchlist, serializer.validated_data["movie_id"])
        return Response(WatchListSerializer(watchlist).data, status=status.HTTP_201_CREATED)


class WatchListMovieDetailView(APIView):
    def delete(self, request, watchlist_id, movie_id):
        watchlist = _load_watchlist(request, watchlist_id)
        services.remove_movie(watchlist, movie_id)
        return Response(status=status.HTTP_204_NO_CONTENT)


class WatchListBulkView(APIView):
    def post(self, request, watchlist_id):
        watchlist = _load_watchlist(request, watchlist_id)
        serializer = BulkUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.bulk_update_movies(
            watchlist,
            serializer.validated_data["add"],
            serializer.validated_data["remove"],
        )
        return Response(WatchListSerializer(watchlist).data)
