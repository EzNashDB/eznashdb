# app/views.py
import json

import sentry_sdk
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.core.management import call_command
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View
from django.views.generic import TemplateView
from sentry_sdk import capture_message, set_context, set_tag

from app.backups.core import list_gdrive_backups
from app.emails import send_appeal_notification
from app.forms import AbuseAppealForm, CaptchaVerificationForm
from app.mixins import HtmxRequestMixin, is_rate_limiting_active
from app.models import AbuseState


def _validated_next(request, raw_next):
    if raw_next and url_has_allowed_host_and_scheme(
        raw_next,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return raw_next
    return "/"


@method_decorator(staff_member_required, name="dispatch")
class AdminDashboardView(TemplateView):
    template_name = "admin/admin_dashboard.html"

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")

        if action == "backup_db":
            try:
                call_command("backup_db")
                messages.success(request, "Database backup completed successfully!")
            except Exception as e:
                messages.error(request, f"Backup failed: {str(e)}")

        return redirect("admin_dashboard")


@method_decorator(staff_member_required, name="dispatch")
class RestoreDBView(TemplateView):
    template_name = "admin/restore_db.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["backups"] = self.list_available_backups()
        return context

    def list_available_backups(self):
        remote_backups = list_gdrive_backups()
        if remote_backups:
            return [
                {
                    "filename": filename,
                    "date": backup_date,
                    "display_date": backup_date.strftime("%B %d, %Y at %I:%M %p"),
                }
                for filename, backup_date in remote_backups
            ]
        return []

    def post(self, request, *args, **kwargs):
        backup_filename = request.POST.get("backup_filename")
        confirmation = request.POST.get("confirmation", "").strip()

        if confirmation != "RESTORE":
            messages.error(request, "Please type RESTORE to confirm.")
            return redirect("restore_db")

        if not backup_filename:
            messages.error(request, "Please select a backup to restore.")
            return redirect("restore_db")

        try:
            # Safety backup before restore
            messages.info(request, "Creating safety backup before restore...")
            call_command("backup_db")

            # Perform restore
            call_command("restore_db", backup_filename)

            messages.success(request, f"Database restored successfully from {backup_filename}")
        except Exception as e:
            messages.error(request, f"Restore failed: {str(e)}")

        return redirect("restore_db")


class ClientErrorReportView(View):
    """Proxy endpoint for client-side error reporting to Sentry."""

    def post(self, request):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        message = data.get("message", "Unknown error")
        stack = data.get("stack", "")
        context = data.get("context", {})
        level = data.get("level", "error")

        try:
            # Add context and tags
            page = context.get("page", {})
            set_context(
                "error_info",
                {
                    "message": message,
                    "stack": stack,
                    "context": context,
                    "user_agent": request.META.get("HTTP_USER_AGENT", ""),
                    "url": page.get("fullUrl", ""),
                },
            )
            set_tag("source", "client")
            set_tag("page", page.get("url", ""))

            # Add user info if authenticated
            user = context.get("user", {})
            if user.get("isAuthenticated"):
                sentry_sdk.set_user({"id": user.get("id"), "username": user.get("username")})

            # Capture the error
            capture_message(f"[Client] {message}\n{stack}", level=level)
            return JsonResponse({"status": "reported"})

        except Exception as e:
            # Don't fail if Sentry reporting fails
            return JsonResponse({"error": str(e)}, status=500)


class CaptchaVerifyView(HtmxRequestMixin, View):
    """
    Dedicated view for CAPTCHA verification.
    After successful verification, marks the user's AbuseState as verified (valid until their
    strikes next change) and redirects to 'next' URL (or triggers abuseCaptchaVerified for htmx
    requests).
    """

    def get_next_url(self):
        raw_next = self.request.POST.get("next") or self.request.GET.get("next")
        return _validated_next(self.request, raw_next)

    def get(self, request):
        form = CaptchaVerificationForm()
        # Auto-bypass CAPTCHA if rate limiting feature is disabled
        if not is_rate_limiting_active(request):
            return redirect(self.get_next_url())
        return render(
            request,
            "eznashdb/captcha_verify.html",
            {
                "form": form,
                "next_url": self.get_next_url(),
            },
        )

    def post(self, request):
        form = CaptchaVerificationForm(request.POST)

        if form.is_valid():
            return self.handle_success(request)
        return self.handle_failure(request, form)

    def handle_success(self, request):
        # Only mark verification if it was actually pending, so a user can't pre-arm a future
        # verification while below the CAPTCHA threshold. Anonymous users are never gated
        # (AbusePreventionMixin short-circuits for them), so there's no state to record.
        if request.user.is_authenticated:
            state = AbuseState.get_or_create(request.user)
            if state.captcha_verification_pending:
                state.mark_captcha_verified()
        if self.is_htmx:
            response = HttpResponse("")
            response["HX-Reswap"] = "none"
            response["HX-Trigger"] = "abuseCaptchaVerified"
            return response
        return HttpResponseRedirect(self.get_next_url())

    def handle_failure(self, request, form):
        message = "CAPTCHA verification failed. Please try again."
        next_url = self.get_next_url()
        if self.is_htmx:
            response = render(
                request,
                "includes/captcha_modal.html",
                {"form": form, "next_url": next_url, "message": message},
            )
            response["HX-Trigger-After-Swap"] = "abuseCaptchaRequired"
            return response
        return render(
            request,
            "eznashdb/captcha_verify.html",
            {"form": form, "next_url": next_url, "message": message},
        )


@method_decorator(login_required, name="dispatch")
class AppealBanView(View):
    """Handle abuse appeal form submissions from the permanent-ban page."""

    def post(self, request):
        """Process appeal submission."""
        form = AbuseAppealForm(request.POST)
        if form.is_valid():
            appeal = form.save()

            send_appeal_notification(appeal)

            messages.success(
                request, "Your appeal has been submitted. We'll review it and get back to you."
            )
            return HttpResponseRedirect("/")

        abuse_state = AbuseState.get_or_create(request.user)
        return render(request, "429.html", {"appeal_form": form, "abuse_state": abuse_state})


def custom_500(request):
    """Custom 500 error handler that provides request context for waffle tags."""

    return render(request, "500.html", status=500)
