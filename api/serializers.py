from rest_framework import serializers
from rest_framework.fields import FileField
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
    yyyy_mm_dd = serializers.StringRelatedField(required=False)
    duration_in_min = serializers.StringRelatedField(required=False)
    subject_title = serializers.StringRelatedField(required=False)
    teacher_username = serializers.StringRelatedField(required=False)
    student_username = serializers.StringRelatedField(required=False)
    pdf = serializers.FileField(required=False)

    def to_internal_value(self, data):
        # errors when mapped directly:
        # [0] since with MultiPartParser, data is a QueryDict
        duration_in_min = int(data.get("duration_in_min", None))
        date = data.get("yyyy_mm_dd", None)
        teacher_username = data.get("teacher_username", None)
        student_username = data.get("student_username", None)

        # no try for subject since get or create
        data["subject"] = Subject.objects.get_or_create(title=data.pop("subject_title"))[0].id

        try:
            data["date"] = self.validate_date(date)
            data["teacher"] = self.validate_user(teacher_username)
            data["student"] = self.validate_user(student_username)
            data["duration"] = self.validate_duration(duration_in_min)
        except serializers.ValidationError as e:
            raise e

        return super().to_internal_value(data)

    class Meta:
        model = Tutoring
        fields = "__all__"

    def validate_date(self, value):
        # Check if valid format
        try:
            input_date = datetime.strptime(str(value), "%Y-%m-%d").date()
        except ValueError:
            raise serializers.ValidationError({"date": f"Invalid date format: {value}"})

        # Check if in past
        if input_date > date.today():
            raise serializers.ValidationError({"date": "Date must be in past."})

        return value

    def validate_user(self, value):
        try:
            return User.objects.get(username=value).id
        except User.DoesNotExist:
            raise serializers.ValidationError({"teacher": "Teacher or Student does not exist."})

    def validate_duration(self, value):
        # Check if duration in (0, 360]
        if value < 1 or value > 360:
            raise serializers.ValidationError({"duration": "Duration must be in (0, 360]."})
        return value

    def validate_pdf(self, value):
        # Check if not provided
        if not value:
            return None

        # Check if other file type
        if not value.name.endswith(".pdf"):
            raise serializers.ValidationError("File must be a PDF.")
        return value
