from rest_framework import serializers

from .models import Movie, WatchList


class MovieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Movie
        fields = ["id", "title", "genre", "release_year"]


class WatchListSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=100, allow_blank=True)
    movies = MovieSerializer(many=True, read_only=True)
    movie_count = serializers.SerializerMethodField()

    class Meta:
        model = WatchList
        fields = ["id", "name", "description", "movies", "movie_count", "created_at", "updated_at"]
        read_only_fields = ["id", "movies", "movie_count", "created_at", "updated_at"]

    def get_movie_count(self, obj):
        return obj.entries.count()


class AddMovieSerializer(serializers.Serializer):
    movie_id = serializers.IntegerField()


class BulkUpdateSerializer(serializers.Serializer):
    add = serializers.ListField(child=serializers.IntegerField(), required=False, default=list)
    remove = serializers.ListField(child=serializers.IntegerField(), required=False, default=list)
