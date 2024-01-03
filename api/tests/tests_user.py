from rest_framework import status
from rest_framework.test import APIClient

from django.contrib.auth.models import Group
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

import os
import json

from checkweb.models import Subject, Tutoring, User
from checkweb.views.views_basic import calc_stundenkosten
from ..serializers import SubjectSerializer


class UserViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.teacher_user = User.objects.create_user(
            username="teacher_user",
            password="password",
            email="teacher@example.com",
            first_name="teacher",
            last_name="user",
        )
        self.teacher_user.groups.set([Group.objects.get(name="Teacher")])

        self.student_user = User.objects.create_user(
            username="student_user",
            password="password",
            email="student@example.com",
            first_name="student",
            last_name="user",
        )

    def test_get_user_teacher(self):
        response = self.client.get(
            reverse("api:user_view", kwargs={"user_id": self.student_user.id})
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_nonexistent_user(self):
        self.client.force_authenticate(user=self.teacher_user)
        response = self.client.get(reverse("api:user_view", kwargs={"user_id": 999}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_post_user_teacher(self):
        self.client.force_authenticate(user=self.teacher_user)
        data = {
            "username": "new_user",
            "password": "password",
            "email": "new_user@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "phone_number": "1234567890",
        }
        response = self.client.post(reverse("api:user_view"), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_post_existing_user_teacher(self):
        self.client.force_authenticate(user=self.teacher_user)
        data = {
            "username": self.student_user.username,
            "password": "password",
            "email": "new_user@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "phone_number": "1234567890",
        }
        response = self.client.post(reverse("api:user_view"), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class DeleteUserViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.teacher_user = User.objects.create_user(
            username="teacher_user",
            password="password",
            email="teacher@example.com",
            first_name="teacher",
            last_name="user",
        )
        self.teacher_user.groups.set([Group.objects.get(name="Teacher")])

        self.student_user = User.objects.create_user(
            username="student_user",
            password="password",
            email="student@example.com",
            first_name="student",
            last_name="user",
        )

    def test_delete_user_teacher(self):
        self.client.force_authenticate(user=self.teacher_user)
        response = self.client.delete(
            reverse("api:delete_user", kwargs={"username": self.student_user.username})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_nonexistent_user(self):
        self.client.force_authenticate(user=self.teacher_user)
        response = self.client.delete(
            reverse("api:delete_user", kwargs={"username": "nonexistent_user"})
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_student_cannot_delete_other_student(self):
        self.client.force_authenticate(user=self.student_user)
        response = self.client.delete(
            reverse("api:delete_user", kwargs={"username": self.teacher_user.username})
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_student_can_delete_self(self):
        self.client.force_authenticate(user=self.student_user)
        response = self.client.delete(
            reverse("api:delete_user", kwargs={"username": self.student_user.username})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
