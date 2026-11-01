class UserIdMiddleware:
    """Copies the X-User-Id header onto the request as `request.user_id` (or None).

    The React frontend sends the logged-in user's id in this header on every call.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.user_id = request.headers.get("X-User-Id") or None
        return self.get_response(request)
