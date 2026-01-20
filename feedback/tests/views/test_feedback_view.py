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


def test_post_success_shows_success_message(
    rf, feedback_data, add_middleware_to_request, mocker, mailoutbox, superuser
):
    """Test that successful submission shows success message and sends email."""
    request = rf.post("/feedback/", feedback_data)
    # Set up messages storage for RequestFactory
    request = add_middleware_to_request(request)

    view = FeedbackView()

    # Mock GitHub client to succeed
    mock_client_instance = mocker.Mock()
    mock_client_instance.create_issue.return_value = {
        "number": 123,
        "html_url": "https://github.com/test/repo/issues/123",
    }
    mocker.patch("feedback.views.GitHubClient", return_value=mock_client_instance)
    mocker.patch("feedback.views.ImgurClient")

    response = view.post(request)

    # Should have added success message to request
    messages = list(request._messages)
    assert len(messages) == 1
    assert str(messages[0]) == "Thanks! We received your feedback and will review it soon."
    assert messages[0].level_tag == "success"
    assert response["HX-Trigger"] == "feedbackSubmitted"

    # Should have sent one email
    assert len(mailoutbox) == 1
    email = mailoutbox[0]
    assert email.subject == "New Feedback Submitted"
    assert email.to == ["admin@example.com"]
    assert email.from_email == "ezratnashimdb@gmail.com"
    # Check that email contains the feedback details (in HTML part)
    html_content = email.alternatives[0][0] if email.alternatives else ""
    assert feedback_data["details"] in html_content
    assert feedback_data["email"] in html_content
    assert feedback_data["current_url"] in html_content
    assert feedback_data["browser_info"] in html_content
    assert "https://github.com/test/repo/issues/123" in html_content


def test_post_github_failure_no_email_sent(
    rf, feedback_data, add_middleware_to_request, mocker, mailoutbox, superuser
):
    """Test that email is not sent when GitHub issue creation fails."""
    request = rf.post("/feedback/", feedback_data)
    # Set up messages storage for RequestFactory
    request = add_middleware_to_request(request)

    view = FeedbackView()

    # Mock GitHub client to fail
    mock_client_instance = mocker.Mock()
    mock_client_instance.create_issue.return_value = None
    mocker.patch("feedback.views.GitHubClient", return_value=mock_client_instance)

    view.post(request)

    # Should have added error message
    messages = list(request._messages)
    assert len(messages) == 1
    assert str(messages[0]) == "Unable to submit feedback. Please try again."
    assert messages[0].level_tag == "danger"

    # Should not have sent any emails
    assert len(mailoutbox) == 0


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
