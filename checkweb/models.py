from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError


class Role(models.Model):
    TITLE_CHOICES = [
        ("Student", "Student"),
        ("Teacher", "Teacher"),
        ("Developer", "Developer"),
    ]
    title = models.CharField(max_length=10, choices=TITLE_CHOICES)

    def __str__(self):
        return self.title

    # Ensure title being in TITLE_CHOICES
    def save(self, *args, **kwargs):
        if self.title not in [choice[0] for choice in self.TITLE_CHOICES]:
            raise ValueError(f"Invalid role title: {self.title}. It must be 'Student', 'Teacher', or 'Developer'.")
        super().save(*args, **kwargs)

    def serialize(self):
        return {"title": self.title}


class User(AbstractUser):
    first_name = models.CharField(max_length=30, blank=False)
    last_name = models.CharField(max_length=30, blank=False)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    email = models.CharField(max_length=32, unique=True, blank=False)
    preis_pro_45 = models.FloatField(null=True, blank=True)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)

    def __str__(self):
        return f"[{self.id}] {self.username}"

    def clean(self):
        if not self.first_name or not self.last_name:
            raise ValidationError("First and Last name must be specified.")
        if not self.email:
            raise ValidationError("Email must be specified.")

    def save(self, *args, **kwargs):
        self.clean()

        # Set default role to "Teacher" if no role is provided
        if not self.role_id:
            self.role, created = Role.objects.get_or_create(title="Student")

        super().save(*args, **kwargs)

    def serialize(self):
        return {
            "username": self.username,
            "id": self.id,
            "phone_number": self.phone_number,
            "preis_pro_45": self.preis_pro_45,
            "role": self.role.serialize(),
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
        if self.teacher and self.teacher.role.title != "Teacher":
            raise ValidationError(
                "Only users with the role 'Teacher' can be assigned as teachers for tutoring sessions."
            )

        if self.student and self.student.role.title != "Student":
            raise ValidationError(
                "Only users with the role 'Student' can be assigned as students for tutoring sessions."
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
