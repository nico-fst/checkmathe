from django.urls import path
from .views import views_basic, views_tutoring, views_permissions, views_user
from rest_framework.authtoken.views import obtain_auth_token

app_name = "api"

urlpatterns = [
    path("get_subjects/", views_basic.get_subjects, name="get_subjects"),
    path("add_subject/", views_basic.add_subject, name="add_subject"),
    path("user_list_view/", views_user.UserListView.as_view(), name="user_list_view"),
    path("obtain_auth_token/", obtain_auth_token, name="obtain_auth_token"),
    path("tutoring_view/<int:tut_id>/", views_tutoring.TutoringView.as_view(), name="tutoring_view"),
    path("user_view/<int:user_id>/", views_user.UserView.as_view(), name="user_view"),
    path("user_view/", views_user.UserView.as_view(), name="user_view"),
    path("delete_user/<str:username>/", views_user.DeleteUserView.as_view(), name="delete_user"),
    path("create_tutoring/", views_tutoring.CreateTutoringView.as_view(), name="create_tutoring"),
    path("sum_view/<str:stud_username>/<int:year>/<int:month>/", views_basic.SumView.as_view(), name="sum_view"),
]
