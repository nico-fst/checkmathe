from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("tutoring", views.tutoring, name="tutoring"),  # only for providing param differently
    path("tutoring/<int:tut_id>", views.tutoring, name="tutoring"),
    path("tutoring_view/<int:tut_id>", views.tutoring_view, name="tutoring_view"),
    path("new_tut", views.new_tut, name="new_tut"),
    path("history", views.history_view, name="history_view"),  # only for providing param differently
    path("history/<int:student_id>", views.history_view, name="history_view"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
]
