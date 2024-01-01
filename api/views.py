from rest_framework.response import Response
from rest_framework import authentication, permissions
from rest_framework.decorators import api_view
from checkweb.models import Subject, User, Tutoring
from .serializers import SubjectSerializer
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from datetime import datetime, date
from rest_framework import status
import re


@api_view(["GET"])
def get_subjects(request):
    subjects = Subject.objects.all()
    serializer = SubjectSerializer(subjects, many=True)  # True: seri multiple items
    return Response(serializer.data)


@api_view(["POST"])
def add_subject(request):
    serializer = SubjectSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
    return Response(serializer.data)


class UserListView(APIView):
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        usernames = [(user.username, user.email) for user in User.objects.all()]
        return Response(usernames)


class IsParticipating(permissions.BasePermission):
    def has_permission(self, request, view):
        try:
            tut_id = view.kwargs.get("tut_id")
            tut = Tutoring.objects.get(id=tut_id)
        except Tutoring.DoesNotExist:
            return False

        return tut.student == request.user or tut.teacher == request.user


class IsTeaching(permissions.BasePermission):
    def has_permission(self, request, view):
        try:
            tut_id = view.kwargs.get("tut_id")
            tut = Tutoring.objects.get(id=tut_id)
        except Tutoring.DoesNotExist:
            return False

        return tut.teacher == request.user


def is_date_valid(date_str):
    try:
        input_date = datetime.strptime(date_str, "%Y-%m-%d").date()  # parse to datetime object
        return input_date <= date.today()
    except ValueError:
        return False


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
                {"error": "Permission denied. Only the teacher of this tutoring may update or delete it."},
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
                {"error": "Permission denied. Only the teacher of this tutoring may update or delete it."},
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
            {"message": f"Tutoring session with id {tut_id} has been modified: {value_dict_as_string}."}
        )


class CreateTutoringView(APIView):
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # Guard: only teacher may create
        if not IsTeaching():
            return Response(
                {"error": "Permission denied. Only teacher may create Tutorings."},
                status=status.HTTP_403_FORBIDDEN,
            )

        new_values = request.data

        # Guard: teach, stud usernames do not exist
        try:
            teach = User.objects.get(username=new_values["teacher_username"])
            stud = User.objects.get(username=new_values["student_username"])
        except User.DoesNotExist:
            return Response(
                {"error": "At least one of the usernames do not exist."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # ... and Guard: they are not in the correct role
        if teach.groups.first().name != "Teacher" or stud.groups.first().name != "Student":
            return Response(
                {"error": "At least one of the users does not fit its role."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Guard: date format invalid
        if not is_date_valid(new_values["YYYY-MM-DD"]):
            return Response(
                {"error": "Date format is not valid or in the future."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # ... and date default: today
        date = new_values["YYYY-MM-DD"]
        if not new_values["YYYY-MM-DD"]:
            date = datetime.today().date()

        # Guard: duration not in (0, 360]
        duration = round(float(new_values["duration_in_min"]))
        if duration < 1 or duration > 360:
            return Response(
                {"error": "Duration must be in (0, 360] Minutes."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Guard: Content empty
        content = new_values["content"]
        if len(content) == 0:
            return Response(
                {"error": "Content must be provided."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # create new subject if necessary
        subject, created = Subject.objects.get_or_create(title=new_values["subject_title"])

        # Guard: recognize duplicate
        if (
            Tutoring.objects.filter(
                date=date,
                duration=duration,
                subject=subject,
                teacher=teach,
                student=stud,
                content=content,
            ).count()
            != 0
        ):
            return Response(
                {"error": "You should not create a duplicate."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            new_tut = Tutoring(
                date=date,
                duration=duration,
                subject=subject,
                teacher=teach,
                student=stud,
                content=content,
            )
            new_tut.save()
        except ValueError as e:
            return Response(
                {"error": e},
                status=status.HTTP_403_FORBIDDEN,
            )

        return Response(new_tut.serialize(), status=status.HTTP_201_CREATED)
