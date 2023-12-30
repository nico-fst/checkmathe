from rest_framework import serializers
from checkweb.models import Role, User, Subject, Tutoring

class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = '__all__'