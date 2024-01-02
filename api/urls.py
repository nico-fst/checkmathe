from django.urls import path
from . import views
from rest_framework.authtoken.views import obtain_auth_token

app_name = "api"

urlpatterns = [
    path("get_subjects/", views.get_subjects, name="get_subjects"),
    path("add_subject/", views.add_subject, name="add_subject"),
    path("user_list_view/", views.UserListView.as_view(), name="user_list_view"),
    path("obtain_auth_token/", obtain_auth_token, name="obtain_auth_token"),
    path("tutoring_view/<int:tut_id>/", views.TutoringView.as_view(), name="tutoring_view"),
    path("user_view/<int:user_id>/", views.UserView.as_view(), name="user_view"),
    path("user_view/", views.UserView.as_view(), name="user_view"),
    path("delete_user/<str:username>/", views.DeleteUserView.as_view(), name="delete_user"),
    path("create_tutoring/", views.CreateTutoringView.as_view(), name="create_tutoring"),
    path("sum_view/<str:stud_username>/<int:year>/<int:month>", views.SumView.as_view(), name="sum_view"),
]
