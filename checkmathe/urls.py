from django.contrib import admin
from django.urls import path, include
from checkweb import views as checkweb_views
from api.views import views_basic as api_views
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="Nico's CheckMathe API",
        default_version="v1",
        description="Mailny for teachers to manipulate Tutoring entities and exchange metadata",
        # terms_of_service="https://www.yourapp.com/terms/",
        contact=openapi.Contact(email="nico.stern@checkmathe.com"),
        # license=openapi.License(name="Your License"),
    ),
    public=True,
)


urlpatterns = [
    # path("admin/", admin.site.urls),
    path("api/", include("api.urls")),
    
    path("swagger/", schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
    
    path("", include("checkweb.urls")),  # statt immer checkweb/ für App einzugeben
]
