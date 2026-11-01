from django.urls import path

from . import views

urlpatterns = [
    path("movies/", views.MovieListView.as_view(), name="movie-list"),
    path("movies/<int:movie_id>/reviews/", views.MovieReviewsView.as_view(), name="movie-reviews"),
    path("reviews/<int:review_id>/", views.ReviewDetailView.as_view(), name="review-detail"),
    path("me/moderation/", views.MyModerationView.as_view(), name="my-moderation"),
]
