import pytest
from rest_framework.test import APIClient

from blog.models import Post, User


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def test_user():
    return User.objects.create(
        name="Test Author",
        email="author@example.com",
        bio="I write about software.",
    )


@pytest.fixture
def post_data():
    return {
        "title": "Debugging Django Like a Pro",
        "content": "Read the failing test first. Then read the code it calls.",
        "excerpt": "A short guide to fixing failing tests.",
        "category": "technology",
        "tags": ["django", "debugging"],
        "readTime": 5,
    }


@pytest.mark.django_db
def test_create_post_with_expected_response_structure_and_values(api_client, test_user, post_data):
    user_id = str(test_user.id)

    response = api_client.post(
        "/api/posts/",
        post_data,
        format="json",
        HTTP_X_USER_ID=user_id,
    )

    assert response.status_code == 201
    assert response.data["message"] == "Post created successfully"

    post = response.data["post"]
    assert "_id" in post
    assert post["title"] == post_data["title"]
    assert post["content"] == post_data["content"]
    assert post["excerpt"] == post_data["excerpt"]
    assert post["category"] == post_data["category"]
    assert post["tags"] == post_data["tags"]
    assert post["readTime"] == post_data["readTime"]
    assert post["published"] is True

    assert post["author"]["_id"] == user_id
    assert post["author"]["name"] == test_user.name
    assert post["author"]["email"] == test_user.email
    assert post["author"]["bio"] == test_user.bio


@pytest.mark.django_db
def test_save_created_post_to_database(api_client, test_user, post_data):
    user_id = str(test_user.id)

    create_response = api_client.post(
        "/api/posts/",
        post_data,
        format="json",
        HTTP_X_USER_ID=user_id,
    )
    assert create_response.status_code == 201

    created_post_id = create_response.data["post"]["_id"]

    saved_post = Post.objects.get(id=created_post_id)
    assert saved_post.title == post_data["title"]
    assert saved_post.content == post_data["content"]
    assert saved_post.category == post_data["category"]
    assert saved_post.tags == post_data["tags"]
    assert saved_post.author_id == test_user.id

    user_posts_response = api_client.get(
        "/api/posts/my-posts/",
        HTTP_X_USER_ID=user_id,
    )
    assert user_posts_response.status_code == 200

    found_post = None
    for post in user_posts_response.data["posts"]:
        if post["_id"] == created_post_id:
            found_post = post
            break

    assert found_post is not None
    assert found_post["title"] == post_data["title"]
