import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class ImgurClient:
    """Client for uploading images to Imgur anonymously."""

    def __init__(self):
        # Imgur Client ID for anonymous uploads (public, safe to commit)
        self.client_id = "546c25a59c58ad7"  # Generic public client ID
        self.upload_url = "https://api.imgur.com/3/upload"

    def upload_image(self, image_file) -> str | None:
        """
        Upload image to Imgur and return the URL.

        Args:
            image_file: Django UploadedFile object

        Returns:
            Image URL if successful, None otherwise
        """
        try:
            headers = {"Authorization": f"Client-ID {self.client_id}"}

            # Read file data
            image_data = image_file.read()
            image_file.seek(0)  # Reset for potential reuse

            files = {"image": image_data}

            response = requests.post(self.upload_url, headers=headers, files=files, timeout=30)
            response.raise_for_status()

            data = response.json()
            if data.get("success"):
                image_url = data["data"]["link"]
                logger.info(f"Uploaded image to Imgur: {image_url}")
                return image_url
            else:
                logger.error(f"Imgur upload failed: {data}")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to upload to Imgur: {e}")
            return None


class GitHubClient:
    """Client for creating GitHub issues via the REST API."""

    def __init__(self):
        self.token = settings.GITHUB_TOKEN
        self.repo = settings.GITHUB_REPO
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
        }

    def create_issue(self, title: str, body: str, labels: list[str]) -> dict | None:
        """
        Create a GitHub issue.

        Args:
            title: Issue title
            body: Issue body (markdown)
            labels: List of label names

        Returns:
            Issue data dict if successful, None otherwise
        """
        if not self.token or not self.repo:
            logger.error("GitHub token or repo not configured")
            return None

        url = f"{self.base_url}/repos/{self.repo}/issues"
        data = {"title": title, "body": body, "labels": labels}

        try:
            response = requests.post(url, json=data, headers=self.headers, timeout=10)
            response.raise_for_status()
            issue_data = response.json()
            logger.info(f"Created GitHub issue #{issue_data['number']}")
            return issue_data
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to create GitHub issue: {e}")
            return None

    def add_screenshot_comment(self, issue_number: int, image_url: str) -> bool:
        """
        Add a comment with screenshot to an existing issue.

        Args:
            issue_number: GitHub issue number
            image_url: URL of the uploaded screenshot

        Returns:
            True if successful, False otherwise
        """
        if not self.token or not self.repo:
            logger.error("GitHub token or repo not configured")
            return False

        try:
            comment_body = f"**Screenshot:**\n\n![screenshot]({image_url})"

            url = f"{self.base_url}/repos/{self.repo}/issues/{issue_number}/comments"
            data = {"body": comment_body}

            response = requests.post(url, json=data, headers=self.headers, timeout=10)
            response.raise_for_status()
            logger.info(f"Added screenshot to issue #{issue_number}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to add screenshot comment: {e}")
            return False
