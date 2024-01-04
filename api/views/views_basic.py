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


class SumView(APIView):
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, stud_username, year, month):
        """returns Tutorings, the number of Tutorings and the sum of money to pay for the provided month

        Args:
            ...
            stud_username (str)
            year: (int)
            month (int)

        Returns:
            {
                "sum": (int),
                "count_tutorings": (int),
                "tutorings": (dict(Tutoring.serializes()) ,
            }
        """

        # Guard: not teacher or participating in Tutoring
        if request.user.groups.first().name != "Teacher" and request.user.username != stud_username:
            return Response(
                {"error": f"You as student may not spectate other Tutorings."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            stud = User.objects.get(username=stud_username)
        except User.DoesNotExist:
            return Response(
                {"error": f"User {stud_username} does not exist."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Guard: user.preis_pro_45 is None
        if stud.preis_pro_45 is None:
            return Response(
                {"error": f"User {stud_username} has no specified preis_pro_45."},
                status=status.HTTP_404_NOT_FOUND,
            )

        tuts = Tutoring.objects.filter(date__year=year, date__month=month, student=stud)

        sum_money = sum(calc_stundenkosten(stud, tut) for tut in tuts)

        return Response(
            {
                "sum": sum_money,
                "count_tutorings": len(tuts),
                "tutorings": [tut.serialize() for tut in tuts],
            }
        )
