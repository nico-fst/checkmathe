from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator


class Role(models.Model):
    TITLE_CHOICES = [
        ("Student", "Student"),
        ("Teacher", "Teacher"),
        ("Admin", "Admin"),
    ]
    title = models.CharField(max_length=10, choices=TITLE_CHOICES)

    def __str__(self):
        return self.title

    # Ensure title being in TITLE_CHOICES
    def save(self, *args, **kwargs):
        if self.title not in [choice[0] for choice in self.TITLE_CHOICES]:
            raise ValueError(f"Invalid role title: {self.title}. It must be 'Student', 'Teacher', or 'Admin'.")
        super().save(*args, **kwargs)

    def serialize(self):
        return {"title": self.title}


class User(AbstractUser):
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    preis_pro_45 = models.FloatField(null=True, blank=True)
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, blank=True, null=True)

    def __str__(self):
        return f"[{self.id}] {self.username}"

    def serialize(self):
        return {
            "username": self.username,
            "user_id": self.id,
            "phone_number": self.phone_number,
            "preis_pro_45": self.preis_pro_45,
            "role": self.role.serialize()
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
    teacher = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="teaching_tutorings"
    )
    student = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="learning_tutorings"
    )
    content = models.TextField()

    def __str__(self):
        return f"[{self.id}] ({self.date}) {self.student} by {self.teacher} [{self.subject}]"

    def serialize(self):
        return {
            "date": self.date,
            "duration": self.duration,
            "subject": self.subject.serialize(),
            "teacher": self.teacher.serialize(),
            "student": self.student.serialize(),
            "content": self.content
        }