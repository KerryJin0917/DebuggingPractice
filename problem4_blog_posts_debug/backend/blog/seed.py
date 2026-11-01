"""Demo data for trying the API by hand:  python manage.py shell -c "import blog.seed"  """
from blog.models import Post, User

alice, _ = User.objects.get_or_create(email="alice@example.com", defaults={"name": "Alice", "bio": "Writes about tech."})
bob, _ = User.objects.get_or_create(email="bob@example.com", defaults={"name": "Bob", "bio": "Travels a lot."})
Post.objects.get_or_create(title="Hello Django", author=alice, defaults={"content": "First post.", "category": "technology"})
Post.objects.get_or_create(title="Lisbon in 3 days", author=bob, defaults={"content": "Trams and tarts.", "category": "travel"})
print(f"alice: X-User-Id: {alice.id}\nbob:   X-User-Id: {bob.id}")
