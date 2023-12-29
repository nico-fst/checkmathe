from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("tutoring/<int:tut_id>", views.tutoring, name="tutoring"),
    path("tutoring_view/<int:tut_id>", views.tutoring_view, name="tutoring_view"),
    path("tutorings/<int:user_id>", views.tutorings, name="tutorings"),
    path("new_tut", views.new_tut, name="new_tut")
]