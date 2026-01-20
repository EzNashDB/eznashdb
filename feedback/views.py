from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import render
from django.views import View

from feedback.forms import FeedbackForm
from feedback.github_client import GitHubClient, ImgurClient

DEFAULT_ISSUE_LABELS = ["user-feedback"]
MAX_TITLE_LENGTH = 80
TITLE_TRUNCATION_SUFFIX = "..."


class FeedbackView(View):
    """Handle feedback form display and submission."""

    template_name = "feedback/feedback_offcanvas.html"

    def get(self, request):
        """Render the feedback form."""
        form = FeedbackForm(
            initial={"email": request.user.email if request.user.is_authenticated else ""}
        )
        return render(request, self.template_name, {"form": form})

    def _generate_issue_title(self, details):
        """Generate a concise title from feedback details."""
        if not details:
            return "Feedback"

        # Use first line or first sentence, whichever is shorter
        lines = details.split("\n")
        first_line = lines[0].strip()

        if "." in first_line:
            first_sentence = first_line.split(".")[0].strip()
            candidate = first_sentence if len(first_sentence) < len(first_line) else first_line
        else:
            candidate = first_line

        if len(candidate) > MAX_TITLE_LENGTH:
            return candidate[: MAX_TITLE_LENGTH - len(TITLE_TRUNCATION_SUFFIX)] + TITLE_TRUNCATION_SUFFIX

        return candidate or "Feedback"

    def _format_issue_body(self, details, current_url, browser_info, email):
        """Format the GitHub issue body."""
        body = (
            f"{details}\n\nSubmitted from: {current_url}\nBrowser: {browser_info}\nEmail: {email or '-'}"
        )
        return body

    def _handle_screenshot_upload(self, screenshot, issue_number, github_client):
        """Upload screenshot to Imgur and add comment to GitHub issue."""
        if not screenshot or not issue_number:
            return

        imgur_client = ImgurClient()
        image_url = imgur_client.upload_image(screenshot)
        if image_url:
            github_client.add_screenshot_comment(issue_number, image_url)

    def _process_feedback_submission(self, cleaned_data):
        """Process valid feedback data and create GitHub issue."""
        details = cleaned_data["details"]
        email = cleaned_data.get("email", "")
        current_url = cleaned_data.get("current_url", "")
        browser_info = cleaned_data.get("browser_info", "")
        screenshot = cleaned_data.get("screenshot")

        # Generate issue title and body
        title = self._generate_issue_title(details)
        body = self._format_issue_body(details, current_url, browser_info, email)

        # Create GitHub client and issue
        client = GitHubClient()
        issue_data = client.create_issue(title=title, body=body, labels=DEFAULT_ISSUE_LABELS.copy())

        if not issue_data:
            return None  # Indicate failure

        # Handle screenshot upload if provided
        self._handle_screenshot_upload(screenshot, issue_data.get("number"), client)

        return issue_data

    def post(self, request):
        """Handle feedback form submission."""
        form = FeedbackForm(request.POST, request.FILES)

        if not form.is_valid():
            # Reload form with field errors
            return render(request, "feedback/feedback_form_fields.html", {"form": form})

        issue_data = self._process_feedback_submission(form.cleaned_data)

        if not issue_data:
            # GitHub API failed
            messages.error(request, "Unable to submit feedback. Please try again.")
            return HttpResponse()

        # Success - trigger event to close offcanvas and show success message
        messages.success(request, "Thanks! We received your feedback and will review it soon.")
        response = HttpResponse()
        response["HX-Trigger"] = "feedbackSubmitted"
        return response
