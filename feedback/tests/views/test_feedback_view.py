from unittest.mock import Mock, patch

import pytest

from feedback.forms import FeedbackForm
from feedback.views import FeedbackView


@pytest.fixture
def feedback_data():
    return {
        "details": "This is a test feedback message that is longer than 50 characters to ensure the form validates properly.",
        "email": "test@example.com",
        "current_url": "https://example.com/test",
        "browser_info": "Test Browser",
        "website": "",
    }


def test_post_form_invalid_renders_form_with_errors(rf, feedback_data):
    """Test that invalid form re-renders form with field errors."""
    # Create invalid form data
    invalid_data = feedback_data.copy()
    invalid_data["details"] = ""  # Make it invalid

    request = rf.post("/feedback/", invalid_data)

    view = FeedbackView()
    response = view.post(request)

    # Should return rendered template with form errors
    assert response.status_code == 200
    assert b"invalid-feedback" in response.content  # Crispy forms adds this for errors
    # Check that form has errors
    form = FeedbackForm(invalid_data)
    assert not form.is_valid()
    assert "details" in form.errors


def test_post_success_shows_success_message(rf, feedback_data, add_middleware_to_request):
    """Test that successful submission shows success message."""
    request = rf.post("/feedback/", feedback_data)
    # Set up messages storage for RequestFactory
    request = add_middleware_to_request(request)

    view = FeedbackView()

    with patch("feedback.views.GitHubClient") as mock_github_client, patch("feedback.views.ImgurClient"):
        # Mock GitHub client to succeed
        mock_client_instance = Mock()
        mock_client_instance.create_issue.return_value = {"number": 123}
        mock_github_client.return_value = mock_client_instance

        response = view.post(request)

        # Should have added success message to request
        messages = list(request._messages)
        assert len(messages) == 1
        assert str(messages[0]) == "Thanks! We received your feedback and will review it soon."
        assert messages[0].level_tag == "success"

        # Should trigger both feedbackSubmitted and refreshMessages events
        assert response["HX-Trigger"] == '{"feedbackSubmitted": "", "refreshMessages": ""}'
