"""HIDDEN TESTS: the grader's extra checks. Don't open until you're done.

    python -m pytest hidden_tests
"""
import pytest
from rest_framework.test import APIClient

from blog.models import Post, User

pytestmark = pytest.mark.django_db


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def alice():
    return User.objects.create(name="Alice", email="alice@example.com", bio="Tech writer.")


@pytest.fixture
def bob():
    return User.objects.create(name="Bob", email="bob@example.com", bio="")


def create(client, user, **overrides):
    data = {"title": "A title", "content": "Some content.", "category": "technology"}
    data.update(overrides)
    return client.post("/api/posts/", data, format="json", HTTP_X_USER_ID=str(user.id))


def make_post(user, **fields):
    defaults = {"title": "Post", "content": "Body", "category": "travel"}
    defaults.update(fields)
    return Post.objects.create(author=user, **defaults)


# --- POST /api/posts/ : validation -----------------------------------------

def test_missing_required_field_returns_400(client, alice):
    response = create(client, alice, category="")
    assert response.status_code == 400
    assert response.data == {"message": "Title, content, and category are required"}
    assert Post.objects.count() == 0


def test_missing_user_header_returns_401(client):
    response = client.post("/api/posts/", {"title": "t", "content": "c", "category": "food"}, format="json")
    assert response.status_code == 401
    assert response.data == {"message": "Not authenticated"}


def test_unknown_user_returns_404(client):
    response = client.post(
        "/api/posts/", {"title": "t", "content": "c", "category": "food"}, format="json", HTTP_X_USER_ID="99999"
    )
    assert response.status_code == 404
    assert response.data == {"message": "User not found"}


def test_invalid_category_returns_400(client, alice):
    response = create(client, alice, category="cooking")
    assert response.status_code == 400
    assert response.data == {"message": "Invalid category"}
    assert Post.objects.count() == 0


# --- POST /api/posts/ : defaults for optional fields ------------------------

def test_read_time_defaults_from_word_count(client, alice):
    long_post = create(client, alice, content="word " * 450)
    short_post = create(client, alice, title="Short", content="just ten words " * 3)
    assert long_post.status_code == 201
    assert long_post.data["post"]["readTime"] == 2
    assert short_post.data["post"]["readTime"] == 1


def test_tags_default_to_empty_list(client, alice):
    response = create(client, alice)
    assert response.status_code == 201
    assert response.data["post"]["tags"] == []
    assert Post.objects.get().tags == []


def test_excerpt_defaults_from_content(client, alice):
    short = create(client, alice, content="Short and sweet.")
    long = create(client, alice, title="Long", content="x" * 400)
    assert short.data["post"]["excerpt"] == "Short and sweet."
    assert long.data["post"]["excerpt"] == "x" * 150 + "..."


def test_ids_are_strings(client, alice):
    post = create(client, alice).data["post"]
    assert post["_id"] == str(Post.objects.get().id)
    assert post["author"]["_id"] == str(alice.id)


# --- GET /api/posts/my-posts/ ------------------------------------------------

def test_my_posts_include_drafts_newest_first(client, alice):
    make_post(alice, title="Old")
    make_post(alice, title="Draft", published=False)
    make_post(alice, title="New")
    response = client.get("/api/posts/my-posts/", HTTP_X_USER_ID=str(alice.id))
    assert response.status_code == 200
    assert [p["title"] for p in response.data["posts"]] == ["New", "Draft", "Old"]


def test_my_posts_only_show_the_callers_posts(client, alice, bob):
    make_post(alice, title="Mine")
    make_post(bob, title="Not mine")
    response = client.get("/api/posts/my-posts/", HTTP_X_USER_ID=str(alice.id))
    assert [p["title"] for p in response.data["posts"]] == ["Mine"]


# --- GET /api/posts/ and /api/posts/<id>/ ----------------------------------

def test_public_feed_hides_drafts(client, alice):
    make_post(alice, title="Live")
    make_post(alice, title="Draft", published=False)
    response = client.get("/api/posts/")
    assert response.status_code == 200
    assert [p["title"] for p in response.data["posts"]] == ["Live"]


def test_get_post_by_id_and_missing_post(client, alice):
    post = make_post(alice, title="Findable")
    found = client.get(f"/api/posts/{post.id}/")
    missing = client.get("/api/posts/99999/")
    assert found.status_code == 200
    assert found.data["post"]["_id"] == str(post.id)
    assert missing.status_code == 404
    assert missing.data == {"message": "Post not found"}


# --- PUT / DELETE /api/posts/<id>/ ----------------------------------------

def test_author_can_update_post(client, alice):
    post = make_post(alice, title="Before")
    response = client.put(
        f"/api/posts/{post.id}/", {"title": "After"}, format="json", HTTP_X_USER_ID=str(alice.id)
    )
    assert response.status_code == 200
    assert response.data["post"]["title"] == "After"
    post.refresh_from_db()
    assert post.title == "After"


def test_author_can_delete_post(client, alice):
    post = make_post(alice)
    response = client.delete(f"/api/posts/{post.id}/", HTTP_X_USER_ID=str(alice.id))
    assert response.status_code == 200
    assert response.data == {"message": "Post deleted successfully"}
    assert not Post.objects.exists()


def test_other_users_cannot_update_or_delete(client, alice, bob):
    post = make_post(alice, title="Alice's")
    url = f"/api/posts/{post.id}/"
    update = client.put(url, {"title": "Hacked"}, format="json", HTTP_X_USER_ID=str(bob.id))
    delete = client.delete(url, HTTP_X_USER_ID=str(bob.id))
    assert update.status_code == 403
    assert delete.status_code == 403
    assert update.data == {"message": "Not authorized"}
    post.refresh_from_db()
    assert post.title == "Alice's"
