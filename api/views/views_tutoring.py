from rest_framework.response import Response
from rest_framework import authentication, permissions
from rest_framework.decorators import api_view
from rest_framework.parsers import JSONParser, FileUploadParser, MultiPartParser
from rest_framework.views import APIView
from rest_framework import serializers, status

from checkweb.models import Subject, User, Tutoring
from checkweb.views.views_basic import calc_stundenkosten

from django.db.models import Q
from django.shortcuts import get_object_or_404
from datetime import datetime, date
import re

from ..serializers import SubjectSerializer, TutoringSerializer, TutoringApiSerializer
from .views_permissions import IsParticipating, IsTeacher, IsTeaching


class TutoringView(APIView):
    """returns, deletes, updates Tutoring

    GET: returns tut if participating
    DELETE: deletes tut if user is teacher of it
    PUT: updates tut if user is teacher of it
    """

    authentication_classes = [authentication.TokenAuthentication]
    parser_classes = [JSONParser, MultiPartParser, FileUploadParser]

    # POSTing a new tut, the teacher can not participate in None
    def get_permissions(self):
        if self.request.method in ["POST"]:
            return [IsTeacher()]
        return [IsTeacher(), IsParticipating()]

    # returns serialized Tutoring
    def get(self, request, tut_id):
        tut = get_object_or_404(Tutoring, id=tut_id)
        return Response(tut.serialize())

    def post(self, request):
        try:
            tut_serializer = TutoringApiSerializer(data=request.data)
            tut_serializer.is_valid(raise_exception=True)
            tut_serializer.save()

            return Response(
                tut_serializer.data,
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            return Response(
                str(e),
                status=status.HTTP_400_BAD_REQUEST,
            )

    def delete(self, request, tut_id):
        tut = get_object_or_404(Tutoring, id=tut_id)
        tut.delete()
        return Response({"message": f"Tutoring session with id {tut_id} has been deleted."})

    # updates values in {new_values} if own teacher
    def put(self, request, tut_id):
        # retrieve provided new values
        tut = get_object_or_404(Tutoring, id=tut_id)
        new_values = request.data.get("new_values", None)

        # update Tutoring
        for key, value in new_values.items():
            setattr(tut, key, value)
        tut.save()

        # provide info about changings
        value_dict_as_string = " ".join([f"{key}: {value}" for key, value in new_values.items()])
        return Response(
            {
                "message": f"Tutoring session with id {tut_id} has been modified: {value_dict_as_string}.",
                "new": tut.serialize(),
            }
        )


class PaidPerMonthView(APIView):
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [IsTeacher]

    def get(self, request, student_username, year, month):
        """Get all Tutorings of specific student of specific year, month
        grouped by paid status
        + if at least one is unpaid"""
        
        tuts = Tutoring.objects.filter(
            teacher=request.user,
            student__username=student_username,
            date__year=year,
            date__month=month,
        )
        
        return Response(
            {
                # if at least one tut should be paid in this month and is not paid yet
                "all_paid": not any(not tut.paid for tut in tuts),
                "paid_tuts": [tut.serialize() for tut in tuts if tut.paid],
                "unpaid_tuts": [tut.serialize() for tut in tuts if not tut.paid],
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        """Set paid status of all Tutorings of specific student of specific year, month to True/False"""
        
        data = request.data

        # Guard: paid must be boolean
        if not isinstance(data.get("paid"), bool):
            return Response(
                {"error": "paid must be boolean"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Guard: year, month must be provided
        if not data.get("year") or not data.get("month"):
            return Response(
                {"error": "year, month must be provided"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Guard: student_username must be valid
        if not User.objects.filter(username=data.get("student_username")).exists():
            return Response(
                {"error": "student_username must be valid"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        tuts = Tutoring.objects.filter(
            teacher=request.user,
            student__username=data.get("student_username"),
            date__year=data.get("year"),
            date__month=data.get("month"),
        )

        for tut in tuts:
            tut.paid = data.get("paid")
            tut.save()

        return Response(
            {
                "message": f"Success changing paid status of Tutorings.",
                "new": [tut.serialize() for tut in tuts],
            }
        )   

class TutoringsView(APIView):
    '''returns all Tutorings of specified User'''

    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FileUploadParser]

    def get(self, request, username):
        user = User.objects.get(username=username)
        tuts = Tutoring.objects.filter(Q(teacher=user) | Q(student=user))

        return Response([tut.serialize() for tut in tuts])
