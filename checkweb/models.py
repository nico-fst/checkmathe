from django.db import models
from django.contrib.auth.models import AbstractUser


class Role(models.Model):
    title = models.CharField(max_length=10)

    def __str__(self):
        return self.title


class User(AbstractUser):
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    preis_pro_45 = models.FloatField(null=True, blank=True)
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, blank=True, null=True)


class Subject(models.Model):
    title = models.CharField(max_length=30)

    def __str__(self):
        return self.title


class Tutoring(models.Model):
    date = models.DateField()
    duration = models.IntegerField()
    subject = models.ForeignKey(Subject, on_delete=models.SET_NULL, null=True)
    teacher = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="teaching_tutorings")
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="learning_tutorings")
    content = models.TextField()

    def __str__(self):
        return f"({self.date}) {self.student} by {self.teacher} [{self.subject}]"
