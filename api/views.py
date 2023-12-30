from rest_framework.response import Response
from rest_framework.decorators import api_view
from checkweb.models import Role, User, Subject, Tutoring
from .serializers import SubjectSerializer

@api_view(["GET"])
def getData(request):
    subjects = Subject.objects.all()
    serializer = SubjectSerializer(subjects, many=True)  # True: serialize multiple items
    return Response(serializer.data)

@api_view(['POST'])
def addSubject(request):
    serializer = SubjectSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
    return Response(serializer.data)