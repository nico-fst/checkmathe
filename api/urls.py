from django.urls import path
from .views import views_basic, views_tutoring, views_permissions, views_user, views_book
from rest_framework.authtoken.views import obtain_auth_token

app_name = "api"

urlpatterns = [
    path("obtain_auth_token/", obtain_auth_token, name="obtain_auth_token"),
    path("subject/", views_basic.SubjectView.as_view(), name="subject"),
    path("tutoring/", views_tutoring.TutoringView.as_view(), name="tutoring"),
    path("tutoring/<int:tut_id>/", views_tutoring.TutoringView.as_view(), name="tutoring"),
    path("user/", views_user.UserView.as_view(), name="user"),
    path("user/<str:username>/", views_user.UserView.as_view(), name="user"),
    path("tuts_per_month/<str:student_username>/", views_tutoring.TutsPerMonthView.as_view(), name="tuts_per_month"),
    path("tuts_per_month/<str:student_username>/<str:year>/<str:month>/", views_tutoring.TutsPerMonthView.as_view(), name="tuts_per_month"),
    # path("book", views_book.BookView.as_view(), name="book"),
]