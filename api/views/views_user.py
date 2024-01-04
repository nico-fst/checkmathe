from rest_framework.response import Response
from rest_framework import authentication, permissions
from rest_framework.decorators import api_view
from rest_framework.parsers import JSONParser, FileUploadParser, MultiPartParser
from rest_framework.views import APIView
from rest_framework import serializers, status

from checkweb.models import Subject, User, Tutoring
from checkweb.views.views_basic import calc_stundenkosten

from django.shortcuts import get_object_or_404
from datetime import datetime, date
import re

from ..serializers import SubjectSerializer, TutoringSerializer, TutoringApiSerializer
from .views_permissions import IsParticipating, IsTeacher, IsTeaching


def is_date_valid(date_str):
    try:
        input_date = datetime.strptime(date_str, "%Y-%m-%d").date()  # parse to datetime object
        return input_date <= date.today()
    except ValueError:
        return False


class UserView(APIView):
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [IsTeacher]

    def get(self, request, username=None):
        # If no user specified, return all usrs
        if not username:
            return Response([user.serialize() for user in User.objects.all()])

        # If specified, return specific user
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response(
                {"error": f"User {username} does not exist."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(user.serialize())

    def post(self, request):
        new_values = request.data

        username = new_values["username"]
        email = new_values["email"]

        # Guard: username or email already exists
        if (
            User.objects.filter(username=username).count() != 0
            or User.objects.filter(email=email).count() != 0
        ):
            return Response(
                {"error": f"User with username {username} or email {email} already exists."},
                status=status.HTTP_403_FORBIDDEN,
            )

        new_user = User.objects.create_user(
            username,
            email,
            new_values["password"],
            first_name=new_values["first_name"],
            last_name=new_values["last_name"],
            phone_number=new_values["phone_number"],
        )
        if "personal_teacher_code" in new_values:
            if new_values["personal_teacher_code"] == "Amaru":
                new_user.groups.set(["Teacher"])

        new_user.save()

        return Response(new_user.serialize(), status=status.HTTP_201_CREATED)

    def delete(self, request, username):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response(
                {"error": f"User {username} does not exist."},
                status=status.HTTP_404_NOT_FOUND,
            )

        user.delete()
        return Response({"message": f"User {username} has been deleted."})
