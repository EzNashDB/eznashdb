# app/views.py
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.management import call_command
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

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
