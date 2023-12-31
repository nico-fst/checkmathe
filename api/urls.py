from django.urls import path
from . import views

urlpatterns = [
    path('', views.getSubject),
    path('addSubject/', views.addSubject)
]