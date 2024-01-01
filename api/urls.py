from django.urls import path
from . import views
from rest_framework.authtoken.views import obtain_auth_token

urlpatterns = [
    path('getSubjects/', views.getSubjects, name="getSubjects"),
    path('addSubject/', views.addSubject, name="addSubject"),
    path('user_list_view/', views.UserListView.as_view(), name='user_list_view'),
    path('obtain_auth_token', obtain_auth_token, name='obtain_auth_token'),
]