from debug_toolbar.toolbar import debug_toolbar_urls
from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.i18n import JavaScriptCatalog

from app.views import (
    AdminDashboardView,
    AppealBanView,
    CaptchaVerifyView,
    ClientErrorReportView,
    RestoreDBView,
    about,
    set_language,
)

# Custom error handler that provides request context
handler500 = "app.views.custom_500"

# Unprefixed: admin, allauth (OAuth callback is a fixed URI in Google Cloud Console), and
# action endpoints with no need for a shareable per-language URL.
urlpatterns = [
    path("accounts/", include("allauth.urls")),
    path("admin/dashboard/", AdminDashboardView.as_view(), name="admin_dashboard"),
    path("admin/restore/", RestoreDBView.as_view(), name="restore_db"),
    path("admin/", admin.site.urls),
    path("appeal/", AppealBanView.as_view(), name="appeal_ban"),
    path("report-error/", ClientErrorReportView.as_view(), name="report_error"),
    path("verify-captcha/", CaptchaVerifyView.as_view(), name="captcha_verify"),
    path("i18n/setlang/", set_language, name="set_language"),
    path("jsi18n/", JavaScriptCatalog.as_view(), name="javascript-catalog"),
]

# Language-prefixed: /en/... and /he/....
urlpatterns += i18n_patterns(
    path("", include("eznashdb.urls")),
    path("about/", about, name="about"),
    path("feedback/", include("feedback.urls")),
    prefix_default_language=True,
)

if settings.DJANGO_ENV != "test":
    urlpatterns = [
        *urlpatterns,
    ] + debug_toolbar_urls()


if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
