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


class SubjectView(APIView):
    def get(self, request):
        """Returns all serialized Subject objects"""
        
        subjects = Subject.objects.all()
        serializer = SubjectSerializer(subjects, many=True)  # True: seri multiple items
        return Response(serializer.data)
    
    def post(self, request):
        """Creates a new Subject object;
        Returns it serialized"""
        
        serializer = SubjectSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
        return Response(serializer.data)