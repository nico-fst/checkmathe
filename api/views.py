from rest_framework.response import Response
from rest_framework import authentication, permissions
from rest_framework.decorators import api_view
from checkweb.models import Subject, User, Tutoring
from .serializers import SubjectSerializer
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from rest_framework import status


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


class TutoringView(APIView):
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated, IsParticipating]

    # returns serialized Tutoring
    def get(self, request, tut_id):
        tut = get_object_or_404(Tutoring, id=tut_id)
        return Response(tut.serialize())

    def delete(self, request, tut_id):
        if not IsTeaching().has_permission(request, self):  # Guard: only teacher may delete
            return Response(
                {"error": "Permission denied. Only the teacher of this tutoring may update or delete it."},
                status=status.HTTP_403_FORBIDDEN,
            )

        tut = get_object_or_404(Tutoring, id=tut_id)
        tut.delete()
        return Response({"message": f"Tutoring session with id {tut_id} has been deleted."})

    # def put(self, reqeust, tut_id):
    #     if not IsTeaching():  # Guard: only teacher may delete
    #         return Response(
    #             {"error": "Permission denied. Only the teacher of this tutoring may update or delete it."},
    #             status=status.HTTP_403_FORBIDDEN,
    #         )
