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


class TutoringView(APIView):
    """returns, deletes, updates Tutoring

    GET: returns tut if participating
    DELETE: deletes tut if user is teacher of it
    PUT: updates tut if user is teacher of it
    """

    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated, IsParticipating]

    # returns serialized Tutoring
    def get(self, request, tut_id):
        tut = get_object_or_404(Tutoring, id=tut_id)
        return Response(tut.serialize())

    def delete(self, request, tut_id):
        # Guard: only teacher may delete
        if not IsTeaching().has_permission(request, self):
            return Response(
                {
                    "error": "Permission denied. Only the teacher of this tutoring may update or delete it."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        tut = get_object_or_404(Tutoring, id=tut_id)
        tut.delete()
        return Response({"message": f"Tutoring session with id {tut_id} has been deleted."})

    # updates values in {new_values} if own teacher
    def put(self, request, tut_id):
        # Guard: only teacher may put
        if not IsTeaching():
            return Response(
                {
                    "error": "Permission denied. Only the teacher of this tutoring may update or delete it."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

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
                "message": f"Tutoring session with id {tut_id} has been modified: {value_dict_as_string}."
            }
        )


class CreateTutoringView(APIView):
    """Creates new Tutoring if requesting User is Teacher and provides valid data

    Parameters:
    - user_data (dict): A dictionary containing information for the new Tutoring instance.
        Example:
        {
            "YYYY-MM-DD": "2024-01-01",
            "duration_in_min": 45,
            "subject_title": "Math",
            "teacher_username": "nico_strn",
            "student_username": "kat_ev",
            "content": "Sinussatz"
        }

    Returns:
    - str: Status message indicating success or failure of creation.

    """

    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [IsTeacher]
    parser_classes = [JSONParser, MultiPartParser, FileUploadParser]

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
