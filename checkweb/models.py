from django.db import models
from django.contrib.auth.models import AbstractUser, Group
from django.core.validators import MinValueValidator, FileExtensionValidator
from django.core.exceptions import ValidationError
from rest_framework.authtoken.models import Token
from django.utils import timezone
from django.urls import reverse
from datetime import date, datetime


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
            "id": self.id,
            "username": self.username,
            "email:": self.email,
            "phone_number": self.phone_number,
            "preis_pro_45": self.preis_pro_45,
            "group": self.groups.first().name,
        }


class Subject(models.Model):
    title = models.CharField(max_length=30, unique=True)

    def __str__(self):
        return self.title

    def serialize(self):
        return {"id": self.id, "title": self.title}


def validate_pdf(value):
    if not value.name.endswith(".pdf"):
        raise ValidationError("Only (one) PDF file allowed.")


class Tutoring(models.Model):
    date = models.DateField(default=timezone.now)
    duration = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)], help_text="Duration must be greater than 0."
    )
    subject = models.ForeignKey(Subject, on_delete=models.SET_NULL, null=True)
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name="teaching_tutorings")
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="learning_tutorings")
    content = models.TextField()
    pdf = models.FileField(upload_to="pdfs/", validators=[validate_pdf], null=True, blank=True)
    paid = models.BooleanField(default=False)

    @property
    def paid_status(self):
        if self.paid:
            return "paid"
        if self.date.year == timezone.now().year and self.date.month == timezone.now().month:
            return "future"
        return "pending"

    def __str__(self):
        return f"[{self.id}] ({self.date}) {self.student} by {self.teacher} [{self.subject}]"

    def clean(self):
        # Ensure only teacher, student user being teacher, student prop
        if self.teacher and self.teacher.groups.first().name != "Teacher":
            raise ValidationError(
                "Only users with the Group 'Teacher' can be assigned as teachers for tutoring sessions."
            )

        if self.student and self.student.groups.first().name != "Student":
            raise ValidationError(
                "Only users with the Group 'Student' can be assigned as students for tutoring sessions."
            )

        # Ensure incoming date:String? getitng saved as date
        if type(self.date) == str:
            self.date = datetime.strptime(self.date, "%Y-%m-%d").date()

    # Checks if valid
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    # for JSON serialization
    def serialize(self):
        return {
            "id": self.id,
            "yyyy-mm-dd": self.date,
            "duration_in_min": self.duration,
            "subject_title": self.subject.title,
            "teacher_username": self.teacher.username,
            "student_username": self.student.username,
            "content": self.content,
            "pdf": "http://127.0.0.1:8000/" + self.pdf.url if self.pdf else None,
            "paid": self.paid,
            "paid_status": self.paid_status,
        }
