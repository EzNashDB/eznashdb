# app/views.py
import json

import sentry_sdk
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.management import call_command
from django.http import JsonResponse
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import TemplateView
from sentry_sdk import capture_message, set_context, set_tag

from app.backups.core import list_gdrive_backups


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
