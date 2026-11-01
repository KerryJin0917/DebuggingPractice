from django.db.models import Avg
from rest_framework import serializers

from .models import Movie, Rating


class MovieSerializer(serializers.ModelSerializer):
    genres = serializers.SlugRelatedField(many=True, read_only=True, slug_field="name")
    average_rating = serializers.SerializerMethodField()

    class Meta:
        model = Movie
        fields = ["id", "title", "release_year", "genres", "average_rating"]

    def get_average_rating(self, obj):
        avg = obj.ratings.aggregate(avg=Avg("score"))["avg"]
        return None if avg is None else round(avg, 2)


class RatingSerializer(serializers.ModelSerializer):
    movie_id = serializers.PrimaryKeyRelatedField(source="movie", queryset=Movie.objects.all())

    class Meta:
        model = Rating
        fields = ["id", "movie_id", "score", "created_at"]
        read_only_fields = ["id", "created_at"]
