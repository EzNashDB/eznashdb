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
        assert response["HX-Trigger"] == "feedbackSubmitted"


def describe_generate_issue_title():
    """Tests for _generate_issue_title method."""

    def test_empty_string_returns_feedback():
        """Test that empty details returns 'Feedback'."""
        view = FeedbackView()
        assert view._generate_issue_title("") == "Feedback"

    def test_uses_first_sentence_when_shorter():
        """Test that first sentence is used when it's shorter than the line."""
        view = FeedbackView()
        details = "Short sentence. This is much longer additional text on the same line"
        result = view._generate_issue_title(details)
        assert result == "Short sentence"

    def test_uses_first_line_when_no_period():
        """Test that first line is used when there's no period."""
        view = FeedbackView()
        details = "This is a line without a period\nSecond line here"
        result = view._generate_issue_title(details)
        assert result == "This is a line without a period"

    def test_uses_first_line_when_shorter_than_first_sentence():
        """Test that first line is used when shorter than first sentence."""
        view = FeedbackView()
        details = "Short\n. Long sentence continues here and keeps going."
        result = view._generate_issue_title(details)
        assert result == "Short"

    def test_truncates_long_titles():
        """Test that titles longer than MAX_TITLE_LENGTH are truncated."""
        view = FeedbackView()
        long_text = "a" * 100
        result = view._generate_issue_title(long_text)
        assert len(result) == 80  # MAX_TITLE_LENGTH
        assert result.endswith("...")
        assert result == "a" * 77 + "..."

    def test_whitespace_stripped():
        """Test that whitespace is properly stripped."""
        view = FeedbackView()
        details = "   Padded title   "
        result = view._generate_issue_title(details)
        assert result == "Padded title"

    def test_empty_first_line_returns_feedback():
        """Test that empty first line returns 'Feedback'."""
        view = FeedbackView()
        details = "\nSecond line"
        result = view._generate_issue_title(details)
        assert result == "Feedback"
