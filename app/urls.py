from debug_toolbar.toolbar import debug_toolbar_urls
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("", include("eznashdb.urls")),
    path("admin/", admin.site.urls),
]

if not settings.TESTING:
    urlpatterns = [
        *urlpatterns,
    ] + debug_toolbar_urls()


if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
