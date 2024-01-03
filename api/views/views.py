from rest_framework.response import Response
from rest_framework import authentication, permissions
from rest_framework.decorators import api_view
from checkweb.models import Subject, User, Tutoring
from ..serializers import SubjectSerializer, TutoringSerializer, TutoringApiSerializer
from rest_framework.views import APIView
from rest_framework import serializers
from django.shortcuts import get_object_or_404
from datetime import datetime, date
from rest_framework import status
from checkweb.views import calc_stundenkosten
from rest_framework.parsers import JSONParser, FileUploadParser, MultiPartParser
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


class UserView(APIView):
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [IsTeacher]

    def get(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {"error": f"User with id {user_id} does not exist."},
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


class DeleteUserView(APIView):
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, username):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response(
                {"error": f"User {username} does not exist."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Guard: user not teacher and tries to delete someone else
        if request.user.groups.first().name != "Teacher" and request.user.username != username:
            return Response(
                {"error": f"You as student may not delete other Users :D."},
                status=status.HTTP_403_FORBIDDEN,
            )

        user.delete()
        return Response({"message": f"User {username} has been deleted."})


class SumView(APIView):
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, stud_username, year, month):
        """returns Tutorings, the number of Tutorings and the sum of money to pay for the provided month

        Args:
            ...
            stud_username (str)
            year (int)
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
