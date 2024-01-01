from rest_framework.response import Response
from rest_framework import authentication, permissions
from rest_framework.decorators import api_view
from checkweb.models import Subject, User
from .serializers import SubjectSerializer
from rest_framework.views import APIView

@api_view(['GET'])
def getSubject(request):
    subjects = Subject.objects.all()
    serializer = SubjectSerializer(subjects, many=True)  # True: seri multiple items
    return Response(serializer.data)

@api_view(['POST'])
def addSubject(request):
    serializer = SubjectSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
    return Response(serializer.data)

class UserListView(APIView):
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, format=None):
        usernames = [(user.username, user.email) for user in User.objects.all()]
        return Response(usernames)