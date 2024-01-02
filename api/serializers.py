from rest_framework import serializers
from checkweb.models import Subject, Tutoring


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = "__all__"


class TutoringSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tutoring
        fields = "__all__"

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation["subject"] = instance.subject.serialize()
        representation["teacher"] = instance.teacher.serialize()
        representation["student"] = instance.student.serialize()
        return representation
