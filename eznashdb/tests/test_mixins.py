from django.contrib.messages import get_messages
from django.urls import reverse


def describe_login_required_mixin():
    """Tests for custom LoginRequiredMixin behavior"""

    def adds_message_for_anonymous_user(client):
        """Test that mixin adds info message when user not authenticated"""
        # Access a protected view (not logged in)
        response = client.get(reverse("eznashdb:create_shul"), follow=True)

        # Should redirect to login with message
        messages = list(response.context["messages"])
        assert len(messages) == 1
        assert "Please log in to add or edit shuls" in str(messages[0])
        assert messages[0].level_tag == "info"

    def does_not_add_message_for_authenticated_user(client, test_user):
        """Test that mixin doesn't add message when user is authenticated"""
        client.force_login(test_user)

        response = client.get(reverse("eznashdb:create_shul"))

        # Should access view directly, no messages
        messages = list(get_messages(response.wsgi_request))
        assert len(messages) == 0
        assert response.status_code == 200
