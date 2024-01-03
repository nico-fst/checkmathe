from django.contrib import admin
from django.urls import path, include
from checkweb import views as checkweb_views
from api.views import views as api_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("api.urls")),
    path("", include("checkweb.urls")),  # statt immer checkweb/ für App einzugeben
]
