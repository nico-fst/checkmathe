from django.test import TestCase, Client
from django.contrib.auth.models import Group
from django.utils import timezone
from ..models import User, Subject, Tutoring
import datetime
from django.urls import reverse
from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError
from rest_framework.authtoken.models import Token
import os


class AuthenticationTestCase(TestCase):
    def setUp(self):
        self.stud = Group.objects.get(name="Student")
        self.teach = Group.objects.get(name="Teacher")

    def test_register_view(self):
        client = Client()

        # Test registration with valid data
        response = client.post(
            reverse("checkweb:register"),
            {
                "username": "testuser",
                "first_name": "Test",
                "last_name": "User",
                "email": "testuser@example.com",
                "phone_number": "+123456789",
                "personal_teacher_code": os.getenv("PERSONAL_TEACHER_CODE"),
                "password": "testpassword",
                "confirmation": "testpassword",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            User.objects.filter(username="testuser").count(), 1
        )  # check wether created

        # Test registration with invalid data (e.g., passwords don't match)
        response = client.post(
            reverse("checkweb:register"),
            {
                "username": "testuser2",
                "first_name": "Test",
                "last_name": "User",
                "email": "testuser2@example.com",
                "phone_number": "+123456789",
                "personal_teacher_code": os.getenv("PERSONAL_TEACHER_CODE"),
                "password": "testpassword",
                "confirmation": "invalidpassword",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            User.objects.filter(username="testuser").count(), 1
        )  # check that not created

    # def test_login_view(self):
    #     client = Client()

    #     # Create a test user
    #     user = User.objects.create_user(
    #         username="testuser",
    #         password="testpassword",
    #         first_name="Xavier",
    #         last_name="X",
    #         email="xavier@mail.de",
    #         phone_number="0176543999",
    #     )

    #     # Test login with valid credentials
    #     response = client.post(reverse("checkweb:login_view"), {"username": "testuser", "password": "testpassword"})

    #     self.assertEqual(response.status_code, 200)
    #     self.assertContains(response, "Login successful")

    #     # Test login with invalid credentials
    #     response = client.post(reverse("checkweb:login_view"), {"username": "testuser", "password": "wrongpassword"})

    #     self.assertEqual(response.status_code, 200)
    #     self.assertContains(response, "Invalid username and/or password.")
