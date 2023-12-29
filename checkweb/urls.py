from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("tutoring/<int:tut_id>", views.tutoring, name="tutoring"),
    path("tutorings/<int:user_id>", views.tutorings, name="tutorings")
]