from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Movie, Rating, WatchedMovie
from .serializers import MovieSerializer, RatingSerializer


class MovieListView(APIView):
    def get(self, request):
        movies = Movie.objects.prefetch_related("genres", "ratings")
        return Response(MovieSerializer(movies, many=True).data)


class MarkWatchedView(APIView):
    def post(self, request, movie_id):
        movie = get_object_or_404(Movie, pk=movie_id)
        _, created = WatchedMovie.objects.get_or_create(user=request.user, movie=movie)
        return Response(
            {"movie_id": movie.pk, "watched": True},
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class RatingCreateView(APIView):
    def post(self, request):
        serializer = RatingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        rating, created = Rating.objects.update_or_create(
            user=request.user,
            movie=serializer.validated_data["movie"],
            defaults={"score": serializer.validated_data["score"]},
        )
        return Response(
            RatingSerializer(rating).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class RecommendationsView(APIView):
    """GET /api/ratings/recommendations/user

    Scaffolding left by the previous dev. See the README for the contract.
    """

    permission_classes = [AllowAny]  # TODO: lock down before release

    def get(self, request):
        return Response({"detail": "Not implemented."}, status=status.HTTP_501_NOT_IMPLEMENTED)
