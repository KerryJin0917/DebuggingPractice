from django.urls import path

from . import views

urlpatterns = [
    path("movies/", views.MovieListView.as_view(), name="movie-list"),
    path("watchlists/", views.WatchListListCreateView.as_view(), name="watchlist-list"),
    path("watchlists/<int:watchlist_id>/", views.WatchListDetailView.as_view(), name="watchlist-detail"),
    path("watchlists/<int:watchlist_id>/movies/", views.WatchListMoviesView.as_view(), name="watchlist-movies"),
    path(
        "watchlists/<int:watchlist_id>/movies/bulk/",
        views.WatchListBulkView.as_view(),
        name="watchlist-movies-bulk",
    ),
    path(
        "watchlists/<int:watchlist_id>/movies/<int:movie_id>/",
        views.WatchListMovieDetailView.as_view(),
        name="watchlist-movie-detail",
    ),
]
