from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

app_name = "checkweb"

urlpatterns = [
    path("", views.index, name="index"),
    path("tutoring", views.tutoring, name="tutoring"),  # only for providing param differently
    path("tutoring/<int:tut_id>", views.tutoring, name="tutoring"),
    path("tutoring_view/<int:tut_id>", views.tutoring_view, name="tutoring_view"),
    path("new_tut", views.new_tut, name="new_tut"),
    path(
        "history_view", views.history_view, name="history_view"
    ),  # only for providing param differently
    path("history_view/<int:student_id>", views.history_view, name="history_view"),
    path("login_view", views.login_view, name="login_view"),
    path("login_demo", views.login_demo, name="login_demo"),
    path("logout_view", views.logout_view, name="logout_view"),
    path("register", views.register, name="register"),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
