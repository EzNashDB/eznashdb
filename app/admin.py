# app/admin.py
from django.contrib import admin, messages
from django.core.management import call_command
from django.shortcuts import redirect
from django.urls import path


def run_backup_view(request):
    if request.method == "POST":
        try:
            call_command("backup_db")
            messages.success(request, "Backup completed successfully!")
        except Exception as e:
            messages.error(request, f"Backup failed: {str(e)}")
    return redirect("/admin/")


# Add custom URL
admin.site.urls  # noqa: B018 This is a property that generates URLs
original_get_urls = admin.site.get_urls


def custom_get_urls():
    urls = original_get_urls()
    custom_urls = [
        path("run-backup/", admin.site.admin_view(run_backup_view), name="run_backup"),
    ]
    return custom_urls + urls


admin.site.get_urls = custom_get_urls

# Your existing model registrations stay the same
# admin.site.register(YourModel, YourModelAdmin)
