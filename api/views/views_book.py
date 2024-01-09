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
from .views_permissions import IsParticipating, IsTeacher, IsTeaching, IsStudent


# class BookView(APIView):
#     authentication_classes = [authentication.TokenAuthentication]
#     permission_classes = [IsStudent]
    
#     def get(self, request):
