from django.db import models
from django.contrib.auth.models import AbstractUser, Group
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from rest_framework.authtoken.models import Token


class User(AbstractUser):
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    preis_pro_45 = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"[{self.id}] {self.username}"

    def save(self, *args, **kwargs):
        # check if username, first, last, email provided
        if not self.username or not self.first_name or not self.last_name or not self.email:
            raise ValidationError("Username, first name, last name, and email are required fields.")

        super().save(*args, **kwargs)

        # Student as default group
        if self.id and not self.groups.exists():
            self.groups.add(Group.objects.get(name="Student"))

    def serialize(self):
        return {
            "username": self.username,
            "id": self.id,
            "phone_number": self.phone_number,
            "preis_pro_45": self.preis_pro_45,
            "group": self.groups.first().name,  # TODO make multiple groups illegal
        }


class Subject(models.Model):
    title = models.CharField(max_length=30)

    def __str__(self):
        return self.title

    def serialize(self):
        return {"title": self.title}


class Tutoring(models.Model):
    date = models.DateField()
    duration = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)], help_text="Duration must be greater than 0."
    )
    subject = models.ForeignKey(Subject, on_delete=models.SET_NULL, null=True)
    teacher = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="teaching_tutorings")
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="learning_tutorings")
    content = models.TextField()

    def __str__(self):
        return f"[{self.id}] ({self.date}) {self.student} by {self.teacher} [{self.subject}]"

    # Ensure only teacher, student user being teacher, student prop
    def clean(self):
        if self.teacher and self.teacher.groups.first().name != "Teacher":
            raise ValidationError(
                "Only users with the Group 'Teacher' can be assigned as teachers for tutoring sessions."
            )

        if self.student and self.student.groups.first().name != "Student":
            raise ValidationError(
                "Only users with the Group 'Student' can be assigned as students for tutoring sessions."
            )

    # Checks if valid
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    # for JSON serialization
    def serialize(self):
        return {
            "id": self.id,
            "date": self.date,
            "duration": self.duration,
            "subject": self.subject.serialize(),
            "teacher": self.teacher.serialize(),
            "student": self.student.serialize(),
            "content": self.content,
        }
