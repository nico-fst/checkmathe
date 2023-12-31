from django.urls import path
from . import views

urlpatterns = [
    path('getSubject/', views.getSubject, name="getSubject"),
    path('addSubject/', views.addSubject, name="addSubject")
]