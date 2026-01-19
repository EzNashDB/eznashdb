from unittest.mock import Mock, patch

import pytest
from django.test import RequestFactory

from feedback.forms import FeedbackForm
from feedback.views import FeedbackView


@pytest.fixture
def rf():
    return RequestFactory()


@pytest.fixture
def feedback_data():
    return {
        "report_type": "bug",
        "description": "Test bug report",
        "email": "test@example.com",
        "current_url": "https://example.com/test",
        "browser_info": "Test Browser",
        "honeypot": "",
    }


class TestFeedbackView:
    def test_post_form_invalid_shows_error_message(self, rf, feedback_data):
        """Test that invalid form shows error message via messages framework."""
        # Create invalid form data
        invalid_data = feedback_data.copy()
        invalid_data["description"] = ""  # Make it invalid

        request = rf.post("/feedback/", invalid_data)
        request._messages = Mock()

        view = FeedbackView()

        # Mock the messages framework
        with patch("feedback.views.messages") as mock_messages:
            response = view.post(request)

            # Should call messages.error
            mock_messages.error.assert_called_once()

            # Should trigger refreshMessages event
            assert response["HX-Trigger"] == '{"refreshMessages": ""}'
            # Middleware will add messages, so content can be empty
            assert response.content == b""

    def test_post_github_api_failure_shows_error_message(self, rf, feedback_data):
        """Test that GitHub API failure shows error message."""
        request = rf.post("/feedback/", feedback_data)
        request._messages = Mock()

        view = FeedbackView()

        # Mock form validation to pass
        mock_form = Mock(spec=FeedbackForm)
        mock_form.is_valid.return_value = True
        mock_form.cleaned_data = feedback_data

        with patch("feedback.views.FeedbackForm", return_value=mock_form), patch(
            "feedback.views.messages"
        ) as mock_messages, patch("feedback.views.GitHubClient") as mock_github_client:
            # Mock GitHub client to fail
            mock_client_instance = Mock()
            mock_client_instance.create_issue.return_value = None
            mock_github_client.return_value = mock_client_instance

            response = view.post(request)

            # Should call messages.error
            mock_messages.error.assert_called_with(
                request, "Unable to submit feedback. Please try again."
            )

            # Should trigger refreshMessages event
            assert response["HX-Trigger"] == '{"refreshMessages": ""}'
            # Middleware will add messages, so content can be empty
            assert response.content == b""

    def test_post_success_shows_success_message(self, rf, feedback_data):
        """Test that successful submission shows success message."""
        request = rf.post("/feedback/", feedback_data)
        request._messages = Mock()

        view = FeedbackView()

        # Mock form validation
        mock_form = Mock(spec=FeedbackForm)
        mock_form.is_valid.return_value = True
        mock_form.cleaned_data = feedback_data

        with patch("feedback.views.FeedbackForm", return_value=mock_form), patch(
            "feedback.views.messages"
        ) as mock_messages, patch("feedback.views.GitHubClient") as mock_github_client, patch(
            "feedback.views.ImgurClient"
        ):
            # Mock GitHub client to succeed
            mock_client_instance = Mock()
            mock_client_instance.create_issue.return_value = {"number": 123}
            mock_client_instance.format_bug_report.return_value = "Formatted bug report"
            mock_client_instance.add_screenshot_comment = Mock()
            mock_github_client.return_value = mock_client_instance

            response = view.post(request)

            # Should call messages.success
            mock_messages.success.assert_called_with(
                request, "Thanks! We received your feedback and will review it soon."
            )

            # Should trigger both feedbackSubmitted and refreshMessages events
            assert response["HX-Trigger"] == '{"feedbackSubmitted": "", "refreshMessages": ""}'
            # Middleware will add messages, so content can be empty
            assert response.content == b""
