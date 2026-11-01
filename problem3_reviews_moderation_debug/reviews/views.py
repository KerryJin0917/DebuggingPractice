from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from . import services
from .models import Movie, Review
from .serializers import MovieSerializer, ReviewSerializer


class MovieListView(APIView):
    def get(self, request):
        movies = Movie.objects.prefetch_related("reviews")
        query = request.query_params.get("q")
        if query:
            movies = movies.filter(title__icontains=query.strip())
        return Response(MovieSerializer(movies, many=True).data)


class MovieReviewsView(APIView):
    def get(self, request, movie_id):
        movie = get_object_or_404(Movie, pk=movie_id)
        return Response(ReviewSerializer(movie.reviews.select_related("author"), many=True).data)

    def post(self, request, movie_id):
        movie = get_object_or_404(Movie, pk=movie_id)
        serializer = ReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        review = services.create_review(request.user, movie, serializer.validated_data)
        return Response(ReviewSerializer(review).data, status=status.HTTP_201_CREATED)


class ReviewDetailView(APIView):
    def patch(self, request, review_id):
        review = get_object_or_404(Review, pk=review_id)
        serializer = ReviewSerializer(review, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        review = services.update_review(request.user, review, serializer.validated_data)
        return Response(ReviewSerializer(review).data)


class MyModerationView(APIView):
    def get(self, request):
        profile = services.get_profile(request.user)
        return Response({"violation_count": profile.violation_count, "is_flagged": profile.is_flagged})
