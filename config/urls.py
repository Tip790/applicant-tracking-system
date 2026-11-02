from django.contrib import admin
from django.urls import include, path


def superuser_only(request):
    """Only superusers may use the Django admin site."""
    return request.user.is_active and request.user.is_superuser


admin.site.has_permission = superuser_only

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path("", include("hiring.urls")),
]
