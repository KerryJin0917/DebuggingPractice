from django.db import models

CATEGORY_CHOICES = [
    ("technology", "Technology"),
    ("lifestyle", "Lifestyle"),
    ("travel", "Travel"),
    ("food", "Food"),
    ("health", "Health"),
    ("business", "Business"),
    ("other", "Other"),
]


class User(models.Model):
    """Blog users. Ported from the old MongoDB backend, so the API still calls ids `_id`."""

    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    bio = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Post(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    excerpt = models.CharField(max_length=500, blank=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts")
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    tags = models.JSONField(default=list, blank=True)
    readTime = models.IntegerField(default=5)
    published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
