from debug_toolbar.toolbar import debug_toolbar_urls
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from app.views import (
    AdminDashboardView,
    AppealBanView,
    CaptchaVerifyView,
    ClientErrorReportView,
    RestoreDBView,
)

# Custom error handler that provides request context
handler500 = "app.views.custom_500"

urlpatterns = [
    path("", include("eznashdb.urls")),
    path("accounts/", include("allauth.urls")),
    path("admin/dashboard/", AdminDashboardView.as_view(), name="admin_dashboard"),
    path("admin/restore/", RestoreDBView.as_view(), name="restore_db"),
    path("admin/", admin.site.urls),
    path("appeal/", AppealBanView.as_view(), name="appeal_ban"),
    path("report-error/", ClientErrorReportView.as_view(), name="report_error"),
    path("verify-captcha/", CaptchaVerifyView.as_view(), name="captcha_verify"),
    path("feedback/", include("feedback.urls")),
]

if settings.DJANGO_ENV != "test":
    urlpatterns = [
        *urlpatterns,
    ] + debug_toolbar_urls()


if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
