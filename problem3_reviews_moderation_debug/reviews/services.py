"""Review creation/editing and the moderation rules around them."""
from rest_framework import status
from rest_framework.exceptions import APIException, PermissionDenied

from .content_checker import find_banned_words
from .models import Review, ReviewerProfile, Violation

FLAG_AFTER_VIOLATIONS = 3


class ContentBlocked(APIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_code = "content_blocked"

    def __init__(self, words):
        super().__init__(
            detail={"detail": "Review contains inappropriate language.", "violated_words": words}
        )


def get_profile(user):
    profile, _ = ReviewerProfile.objects.get_or_create(user=user)
    return profile


def moderate(user, text):
    """Raise if ``user`` may not publish ``text``. Records a violation when blocked."""
    profile = get_profile(user)
    words = find_banned_words(text)
    if words:
        if profile.is_flagged:
            raise PermissionDenied("Your account is flagged.")
        profile.violation_count += 1
        Violation.objects.create(user=user, text=text, words=",".join(words))
        if profile.violation_count > FLAG_AFTER_VIOLATIONS:
            profile.is_flagged = True
        raise ContentBlocked(words)


def create_review(user, movie, data):
    moderate(user, data["body"])
    return Review.objects.create(movie=movie, author=user, **data)


def update_review(user, review, data):
    moderate(user, review.body)
    for field in ("rating", "body"):
        if field in data:
            setattr(review, field, data[field])
    review.save()
    return review
