# app/views.py
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.management import call_command
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView


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

        # Easy to add more actions later:
        # elif action == 'clear_cache':
        #     cache.clear()
        #     messages.success(request, 'Cache cleared!')

        return redirect("admin_dashboard")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Could add context here later (last backup time, system stats, etc.)
        return context
