from rest_framework import serializers

from .models import Movie, Review


class MovieSerializer(serializers.ModelSerializer):
    average_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()

    class Meta:
        model = Movie
        fields = ["id", "title", "release_year", "average_rating", "review_count"]

    def get_average_rating(self, obj):
        ratings = [review.rating for review in obj.reviews.all()]
        return round(sum(ratings) / len(ratings), 2) if ratings else None

    def get_review_count(self, obj):
        return obj.reviews.count()


class ReviewSerializer(serializers.ModelSerializer):
    author = serializers.CharField(source="author.username", read_only=True)
    movie_id = serializers.IntegerField(source="movie.id", read_only=True)
    rating = serializers.IntegerField(min_value=1, max_value=5)
    body = serializers.CharField(max_length=5000)

    class Meta:
        model = Review
        fields = ["id", "movie_id", "author", "rating", "body", "created_at", "updated_at"]
        read_only_fields = ["id", "movie_id", "author", "created_at", "updated_at"]
