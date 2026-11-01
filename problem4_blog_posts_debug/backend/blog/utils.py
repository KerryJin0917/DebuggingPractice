"""Helpers shared by the blog views."""

WORDS_PER_MINUTE = 200
EXCERPT_LENGTH = 150


def get_user_id(request):
    """The caller's user id from the X-User-Id header (set by UserIdMiddleware), or None."""
    return getattr(request, "user_id", None)


def calculate_read_time(content):
    # ~200 words per minute, never less than 1 minute
    return max(1, len(content.split()) // WORDS_PER_MINUTE)


def make_excerpt(content):
    """Default excerpt: the first 150 characters, with "..." only if the content was cut."""
    return content[:EXCERPT_LENGTH] + "..."


def is_author(post, user_id):
    return post.author_id == user_id


def serialize_user(user):
    return {
        "_id": user.id,
        "name": user.name,
        "email": user.email,
        "bio": user.bio,
    }


def serialize_post(post):
    return {
        "id": post.id,
        "title": post.title,
        "content": post.content,
        "category": post.category,
        "tags": post.tags,
        "readTime": post.readTime,
        "published": post.published,
        "author": serialize_user(post.author),
        "createdAt": post.created_at.isoformat(),
        "updatedAt": post.updated_at.isoformat(),
    }
