from datetime import datetime

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.template.loader import render_to_string

User = get_user_model()


def send_appeal_notification(appeal):
    """Send email to all superusers when new appeal is submitted."""
    # Get all superuser emails
    superuser_emails = list(
        User.objects.filter(is_superuser=True).exclude(email="").values_list("email", flat=True)
    )

    if not superuser_emails:
        # No superusers with email configured
        return

    # Use snapshot data for accurate representation of what user was appealing
    snapshot = appeal.state_snapshot

    # Calculate time span from snapshot timestamps if available
    time_span = None
    episode_started = snapshot.get("episode_started_at")
    last_violation = snapshot.get("last_violation_at")
    if episode_started and last_violation:
        start = datetime.fromisoformat(episode_started)
        end = datetime.fromisoformat(last_violation)
        time_span = end - start

    subject = f"New Abuse Appeal from {appeal.abuse_state.user.email}"

    # Render HTML email from template
    html_message = render_to_string(
        "email/abuse_appeal.html",
        {
            "appeal": appeal,
            "snapshot": snapshot,
            "time_span": time_span,
            "admin_url": f"{settings.SITE_URL}/admin/app/abuseappeal/{appeal.id}/change/",
        },
    )

    send_mail(
        subject,
        "",  # Plain text body (empty since we're sending HTML)
        settings.DEFAULT_FROM_EMAIL,
        superuser_emails,
        fail_silently=False,
        html_message=html_message,
    )


def send_feedback_notification(details, user_email, current_url, browser_info, issue_data):
    """Send email to all superusers when new feedback is submitted."""
    # Get all superuser emails
    superuser_emails = list(
        User.objects.filter(is_superuser=True).exclude(email="").values_list("email", flat=True)
    )

    if not superuser_emails:
        # No superusers with email configured
        return

    subject = "New Feedback Submitted"

    # Render HTML email from template
    html_message = render_to_string(
        "email/feedback_notification.html",
        {
            "details": details,
            "user_email": user_email,
            "current_url": current_url,
            "browser_info": browser_info,
            "issue_data": issue_data,
            "issue_url": issue_data.get("html_url") if issue_data else None,
        },
    )

    send_mail(
        subject,
        "",  # Plain text body (empty since we're sending HTML)
        settings.DEFAULT_FROM_EMAIL,
        superuser_emails,
        fail_silently=True,  # Don't fail feedback submission if email fails
        html_message=html_message,
    )
