from rest_framework.response import Response
from rest_framework import authentication, permissions
from rest_framework.decorators import api_view
from rest_framework.parsers import JSONParser, FileUploadParser, MultiPartParser
from rest_framework.views import APIView
from rest_framework import serializers, status

from checkweb.models import Subject, User, Tutoring

from django.shortcuts import get_object_or_404
from datetime import datetime, date
import re

from ..serializers import SubjectSerializer, TutoringSerializer, TutoringApiSerializer


class IsParticipating(permissions.BasePermission):
    """Is requesting User Student or Teacher in Tutoring with tut_id?"""

    def has_permission(self, request, view):
        try:
            tut_id = view.kwargs.get("tut_id")
            tut = Tutoring.objects.get(id=tut_id)
        except Tutoring.DoesNotExist:
            return False

        return tut.student == request.user or tut.teacher == request.user


class IsTeaching(permissions.BasePermission):
    """Is requesting User the teacher of the Tutoring with tut_id?"""

    def has_permission(self, request, view):
        try:
            tut_id = view.kwargs.get("tut_id")
            tut = Tutoring.objects.get(id=tut_id)
        except Tutoring.DoesNotExist:
            return False

        return tut.teacher == request.user


class IsTeacher(permissions.BasePermission):
    "Is requesting User in Group Teacher?"

    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return request.user.groups.filter(name="Teacher").exists()
        return False


class IsStudent(permissions.BasePermission):
    "Is requesting User in Group Student??"

    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return request.user.groups.filter(name="Student").exists()
        return False
