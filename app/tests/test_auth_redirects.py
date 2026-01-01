from bs4 import BeautifulSoup
from django.urls import reverse


def describe_redirect_preservation():
    """Tests for preserving ?next= parameter through authentication flows"""

    def preserves_redirect_from_login_to_signup(client):
        """Signup link on login page preserves ?next= parameter"""
        login_url = reverse("account_login") + f"?next={reverse('eznashdb:create_shul')}"
        response = client.get(login_url)

        soup = BeautifulSoup(response.content, "html.parser")
        signup_link = soup.find("a", string=lambda text: text and "Sign up" in text)
        assert "next=" in signup_link["href"]
        assert reverse("eznashdb:create_shul") in signup_link["href"]

    def preserves_redirect_from_signup_to_login(client):
        """Login link on signup page preserves ?next= parameter"""
        signup_url = reverse("account_signup") + f"?next={reverse('eznashdb:create_shul')}"
        response = client.get(signup_url)

        soup = BeautifulSoup(response.content, "html.parser")
        login_link = soup.find("a", string=lambda text: text and "Log in" in text)
        assert "next=" in login_link["href"]
        assert reverse("eznashdb:create_shul") in login_link["href"]
