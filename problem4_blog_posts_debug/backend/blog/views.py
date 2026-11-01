from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import CATEGORY_CHOICES, Post, User
from .utils import (
    calculate_read_time,
    get_user_id,
    is_author,
    make_excerpt,
    serialize_post,
)

VALID_CATEGORIES = {value for value, _label in CATEGORY_CHOICES}
EDITABLE_FIELDS = ["title", "content", "excerpt", "category", "tags", "readTime", "published"]


# ---------------------------------------------------------------------------
# /api/posts/
# ---------------------------------------------------------------------------

@api_view(["GET", "POST"])
def posts(request):
    if request.method == "POST":
        return create_post(request)
    return list_posts(request)


def list_posts(request):
    """Public feed: published posts only, newest first. Optional ?category= filter."""
    try:
        queryset = Post.objects.select_related("author").order_by("-created_at", "-id")
        category = request.query_params.get("category")
        if category:
            queryset = queryset.filter(category=category)
        return Response({"posts": [serialize_post(post) for post in queryset]})
    except Exception as e:
        return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def create_post(request):
    try:
        user_id = get_user_id(request)
        if not user_id:
            return Response({"message": "Not authenticated"}, status=status.HTTP_401_UNAUTHORIZED)

        if not title or not content or not category:
            return Response(
                {"message": "Title, content, and category are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = request.data
        title = data.get("title")
        content = data.get("content")
        category = data.get("category")
        excerpt = data.get("excerpt")
        tags = data.get("tags")
        readTime = data.get("readTime")

        if readTime:
            readTime = calculate_read_time(content)

        if not excerpt:
            excerpt = make_excerpt(content)

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        post = Post.objects.create(
            title=title,
            content=content,
            excerpt=excerpt,
            category=category,
            tags=tags,
            readTime=readTime,
            author=user,
        )
        post.save()

        return Response(
            {"message": "Post created successfully", "post": post},
            status=status.HTTP_201_CREATED,
        )
    except Exception as e:
        return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ---------------------------------------------------------------------------
# /api/posts/my-posts/
# ---------------------------------------------------------------------------

@api_view(["GET"])
def get_my_posts(request):
    """The caller's own posts, drafts included, newest first."""
    try:
        user_id = get_user_id(request)
        if not user_id:
            return Response({"message": "Not authenticated"}, status=status.HTTP_401_UNAUTHORIZED)

        my_posts = Post.objects.filter(author_id=user_id, published=True).order_by("-created_at", "-id")

        posts_data = []
        for p in my_posts:
            posts_data.append({
                "id": p.id,
                "title": p.title,
                "excerpt": p.excerpt,
                "category": p.category,
                "tags": p.tags,
                "readTime": p.readTime,
                "published": p.published,
                "createdAt": p.created_at.isoformat(),
            })
        return Response({"posts": posts_data}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ---------------------------------------------------------------------------
# /api/posts/<post_id>/
# ---------------------------------------------------------------------------

@api_view(["GET", "PUT", "DELETE"])
def post_detail(request, post_id):
    if request.method == "GET":
        return get_post(request, post_id)
    if request.method == "PUT":
        return update_post(request, post_id)
    return delete_post(request, post_id)


def get_post(request, post_id):
    try:
        post = Post.objects.select_related("author").get(id=post_id)
        return Response({"post": serialize_post(post)})
    except Exception as e:
        return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def update_post(request, post_id):
    try:
        try:
            post = Post.objects.select_related("author").get(id=post_id)
        except Post.DoesNotExist:
            return Response({"message": "Post not found"}, status=status.HTTP_404_NOT_FOUND)

        if not is_author(post, get_user_id(request)):
            return Response({"message": "Not authorized"}, status=status.HTTP_403_FORBIDDEN)

        if "category" in request.data and request.data["category"] not in VALID_CATEGORIES:
            return Response({"message": "Invalid category"}, status=status.HTTP_400_BAD_REQUEST)

        for field in EDITABLE_FIELDS:
            if field in request.data:
                setattr(post, field, request.data[field])
        post.save()
        return Response({"message": "Post updated successfully", "post": serialize_post(post)})
    except Exception as e:
        return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def delete_post(request, post_id):
    try:
        try:
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            return Response({"message": "Post not found"}, status=status.HTTP_404_NOT_FOUND)

        if not is_author(post, get_user_id(request)):
            return Response({"message": "Not authorized"}, status=status.HTTP_403_FORBIDDEN)

        post.delete()
        return Response({"message": "Post deleted successfully"})
    except Exception as e:
        return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
