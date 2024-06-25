from rest_framework.response import Response
from rest_framework import authentication, permissions
from rest_framework.decorators import api_view
from rest_framework.parsers import JSONParser, FileUploadParser, MultiPartParser
from rest_framework.views import APIView
from rest_framework import serializers, status

from checkweb.models import Subject, User, Tutoring
from checkweb.views.views_basic import calc_stundenkosten, calc_serienkosten

from django.contrib.auth.models import Group
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

class TutsPerMonthView(APIView):
    '''GET: returns all Tutorings of student_username grouped by month if provided (else all)'''
    
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def specific_month(self, request, stud: object, year, month):
        tuts_all = Tutoring.objects.filter(student=stud, date__year=year, date__month=month)
        tuts_paid = Tutoring.objects.filter(student=stud, paid=True, date__year=year, date__month=month)
        tuts_unpaid = Tutoring.objects.filter(student=stud, paid=False, date__year=year, date__month=month)

        return Response(
            {
                "tuts_all": [tut.serialize() for tut in tuts_all],
                "tuts_paid": [tut.serialize() for tut in tuts_paid],
                "tuts_unpaid": [tut.serialize() for tut in tuts_unpaid],
                "sum_all": calc_serienkosten(stud, sum([tut.duration for tut in tuts_all])),
                "sum_paid": calc_serienkosten(stud, sum([tut.duration for tut in tuts_paid])),
                "sum_unpaid": calc_serienkosten(stud, sum([tut.duration for tut in tuts_unpaid])),
                "is_paid": tuts_unpaid.count() == 0
            }
        )

    def get(self, request, student_username, year=None, month=None):
        '''get tuts of student_username grouped by month'''

        # Guard: block if student tries to view other tuts
        if (not request.user.groups.filter(name="Teacher").exists()):
            if request.user.username != student_username:
                return Response(
                    {"error": "You as student may not spectate other Tutorings."},
                    status=status.HTTP_403_FORBIDDEN,
                )

        stud = User.objects.get(username=student_username)
        tuts = Tutoring.objects.filter(student=stud)
        collect_yyyy_mm = {}
        resp = {}
        
        # if specific month or broken request
        if year and month:
            return self.specific_month(request, stud, year, month)
        elif (not year and month) or (year and not month):
            return Response(
                {"error": "Provide year and month both or none of them."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # TODO daaaamn inefficient
        # group tuts by month and aggregate infos
        for tut in tuts:
            collect_yyyy_mm[tut.date.strftime("%Y-%m")] = True
        for yyyy_mm, tut in collect_yyyy_mm.items():
            resp[yyyy_mm] = {}
            resp[yyyy_mm]["tuts_all"] = [tut.serialize()
                for tut in Tutoring.objects.filter(
                    student=stud,
                    date__year=yyyy_mm[:4],
                    date__month=yyyy_mm[5:7],
                )
            ]
            resp[yyyy_mm]["tuts_paid"] = [
                tut.serialize()
                for tut in Tutoring.objects.filter(
                    student=stud,
                    date__year=yyyy_mm[:4],
                    date__month=yyyy_mm[5:7],
                    paid=True,
                )
            ]
            resp[yyyy_mm]["tuts_unpaid"] = [
                tut.serialize()
                for tut in Tutoring.objects.filter(
                    student=stud,
                    date__year=yyyy_mm[:4],
                    date__month=yyyy_mm[5:7],
                    paid=False,
                )
            ]
            resp[yyyy_mm]["sum_all"] = calc_serienkosten(stud, sum([tut["duration_in_min"] for tut in resp[yyyy_mm]["tuts_all"]]))
            resp[yyyy_mm]["sum_paid"] = calc_serienkosten(stud, sum([tut["duration_in_min"] for tut in resp[yyyy_mm]["tuts_paid"]]))
            resp[yyyy_mm]["sum_unpaid"] = calc_serienkosten(stud, sum([tut["duration_in_min"] for tut in resp[yyyy_mm]["tuts_unpaid"]]))
            resp[yyyy_mm]["is_paid"] = resp[yyyy_mm]["sum_unpaid"] == 0

        return Response(resp, status=status.HTTP_200_OK)

    def post(self, request, student_username):
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
        if not User.objects.filter(username=student_username).exists():
            return Response(
                {"error": "student_username must be valid"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        tuts = Tutoring.objects.filter(
            teacher=request.user,
            student__username=student_username,
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

