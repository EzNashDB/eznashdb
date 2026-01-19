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
        "details": "Test feedback",
        "email": "test@example.com",
        "current_url": "https://example.com/test",
        "browser_info": "Test Browser",
        "honeypot": "",
    }


class TestFeedbackView:
    def test_post_form_invalid_renders_form_with_errors(self, rf, feedback_data):
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

    def test_post_success_shows_success_message(self, rf, feedback_data):
        """Test that successful submission shows success message."""
        request = rf.post("/feedback/", feedback_data)
        request._messages = Mock()

        view = FeedbackView()

        # Mock form validation
        mock_form = Mock(spec=FeedbackForm)
        mock_form.is_valid.return_value = True
        mock_form.cleaned_data = feedback_data.copy()

        with patch("feedback.views.FeedbackForm", return_value=mock_form), patch(
            "feedback.views.messages"
        ) as mock_messages, patch("feedback.views.GitHubClient") as mock_github_client, patch(
            "feedback.views.ImgurClient"
        ):
            # Mock GitHub client to succeed
            mock_client_instance = Mock()
            mock_client_instance.create_issue.return_value = {"number": 123}
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
