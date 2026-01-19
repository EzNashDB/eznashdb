import logging

from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import render
from django.views import View

from feedback.forms import FeedbackForm
from feedback.github_client import GitHubClient, ImgurClient

logger = logging.getLogger(__name__)

# Default labels applied to all GitHub issues
DEFAULT_ISSUE_LABELS = ["user-feedback"]


class FeedbackView(View):
    """Handle feedback form display and submission."""

    template_name = "feedback/feedback_offcanvas.html"

    def get(self, request):
        """Render the feedback form."""
        form = FeedbackForm(
            initial={
                "email": request.user.email if request.user.is_authenticated else "",
            }
        )
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        """Handle feedback form submission."""
        form = FeedbackForm(request.POST, request.FILES)

        if not form.is_valid():
            # Don't swap - just show errors via messages
            error_msgs = "; ".join(
                [f"{field}: {', '.join(errors)}" for field, errors in form.errors.items()]
            )
            messages.error(request, error_msgs)
            response = HttpResponse()
            response["HX-Trigger"] = '{"refreshMessages": ""}'
            return response

        # Extract form data
        report_type = form.cleaned_data["report_type"]
        email = form.cleaned_data.get("email", "")
        current_url = form.cleaned_data.get("current_url", "")
        browser_info = form.cleaned_data.get("browser_info", "")
        screenshot = form.cleaned_data.get("screenshot")

        # Get description and auto-generate title
        description = form.cleaned_data["description"]

        # Generate title from first sentence/line (up to 80 chars)
        title = description.split("\n")[0]  # First line
        title = title.split(".")[0]  # Or first sentence
        title = (title[:77] + "...") if len(title) > 80 else title
        title = title.strip() or "Feedback"  # Fallback if empty

        # Create GitHub client
        client = GitHubClient()

        # Format issue body based on report type
        if report_type == "bug":
            body = client.format_bug_report(
                description=description,
                current_url=current_url,
                browser_info=browser_info,
                email=email,
            )
        else:  # feature
            body = client.format_feature_request(
                description=description,
                current_url=current_url,
                email=email,
            )

        # Create GitHub issue
        labels = DEFAULT_ISSUE_LABELS.copy()
        if report_type == "bug":
            labels.append("bug")
        else:
            labels.append("enhancement")

        issue_data = client.create_issue(title=title, body=body, labels=labels)

        if not issue_data:
            # GitHub API failed
            messages.error(request, "Unable to submit feedback. Please try again.")
            response = HttpResponse()
            response["HX-Trigger"] = '{"refreshMessages": ""}'
            return response

        # Upload screenshot if provided
        if screenshot and issue_data:
            imgur_client = ImgurClient()
            image_url = imgur_client.upload_image(screenshot)
            if image_url:
                client.add_screenshot_comment(issue_data["number"], image_url)

        # Success - trigger event to close offcanvas and show success message
        messages.success(request, "Thanks! We received your feedback and will review it soon.")
        response = HttpResponse()
        response["HX-Trigger"] = '{"feedbackSubmitted": "", "refreshMessages": ""}'
        return response
