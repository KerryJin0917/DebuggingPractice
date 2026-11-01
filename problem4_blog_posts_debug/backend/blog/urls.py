from django.urls import path

from . import views

urlpatterns = [
    path("posts/", views.posts, name="posts"),
    path("posts/<str:post_id>/", views.post_detail, name="post-detail"),
    path("posts/my-posts/", views.get_my_posts, name="my-posts"),
]
