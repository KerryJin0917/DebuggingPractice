from django.urls import path

from . import views

urlpatterns = [
    path("movies/", views.MovieListView.as_view(), name="movie-list"),
    path("movies/<int:movie_id>/watched/", views.MarkWatchedView.as_view(), name="movie-watched"),
    path("ratings/", views.RatingCreateView.as_view(), name="rating-create"),
    path(
        "ratings/recommendations/user",
        views.RecommendationsView.as_view(),
        name="recommendations-user",
    ),
]
