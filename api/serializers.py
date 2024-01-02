from rest_framework import serializers
from checkweb.models import Subject, Tutoring, User
from django.utils import timezone
from datetime import datetime, date
from django.core.exceptions import ObjectDoesNotExist


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = "__all__"


# TODO not tested
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


class TutoringApiSerializer(serializers.ModelSerializer):
    yyyy_mm_dd = serializers.IntegerField(required=False)
    duration_in_min = serializers.IntegerField(required=False)
    subject_title = serializers.StringRelatedField(required=False)
    teacher_username = serializers.StringRelatedField(required=False)
    student_username = serializers.StringRelatedField(required=False)

    def to_internal_value(self, data):
        # errors when mapped directly:
        data["duration"] = data.pop("duration_in_min", None)
        date = data.pop("yyyy_mm_dd", None)
        data["subject"] = Subject.objects.get_or_create(title=data.pop("subject_title"))[0].id
        teacher_username = data.pop("teacher_username", None)
        student_username = data.pop("student_username", None)

        try:
            data["date"] = self.validate_date(date)
            data["teacher"] = self.validate_user(teacher_username)
            data["student"] = self.validate_user(student_username)
        except serializers.ValidationError as e:
            raise str(e)
        
        return super().to_internal_value(data)

    class Meta:
        model = Tutoring
        fields = "__all__"

    def validate_date(self, value):
        # Check if valid format
        try:
            input_date = datetime.strptime(str(value), "%Y-%m-%d").date()
        except ValueError:
            raise serializers.ValidationError("Invalid date format.")

        # Check if in past
        if input_date > date.today():
            raise serializers.ValidationError("Date must be in past.")

        return value

    def validate_user(self, value):
        try:
            return User.objects.get(username=value).id
        except User.DoesNotExist:
            raise serializers.ValidationError({"error": "Teacher or Student does not exist."})
