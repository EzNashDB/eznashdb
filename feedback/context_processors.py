from feedback.forms import FeedbackForm


def feedback_form(request):
    """Add feedback form to template context."""
    initial = {}
    if hasattr(request, "user") and request.user.is_authenticated:
        initial["email"] = request.user.email
    return {"feedback_form": FeedbackForm(initial=initial)}
