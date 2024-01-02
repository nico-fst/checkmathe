from django.test import TestCase, Client
from django.contrib.auth.models import Group
from django.utils import timezone
from ..models import User, Subject, Tutoring
import datetime
from django.urls import reverse
from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError
from rest_framework.authtoken.models import Token


class DB_ConsistencyTestCase(TestCase):
    def setUp(self):
        self.stud = Group.objects.get(name="Student")
        self.teach = Group.objects.get(name="Teacher")

        self.thore = User.objects.create_user(
            "Thore.st",
            "thore@mail.de",
            "password",
            first_name="Thore",
            last_name="St",
            phone_number="+49176999",
            preis_pro_45=20,
        )
        self.thore.groups.set([self.stud])

        self.xavier = User.objects.create(
            username="Xavier.x",
            first_name="Xavier",
            last_name="X",
            email="xavier.x@mail.de",
            phone_number="0176543999",
        )
        self.xavier.groups.set([self.teach])

        self.tut = Tutoring.objects.create(
            date=timezone.now().date(),
            duration=45,
            subject=Subject.objects.create(title="Math"),
            student=self.thore,
            teacher=self.xavier,
            content="labore culpa reprehenderit sit officia elit voluptate sit ad sit",
        )

    def test_incomplete_creation(self):
        with self.assertRaises(ValidationError):
            teach_empty = User.objects.create()
        with self.assertRaises(ValidationError):
            teach_without_email = User.objects.create(
                username="Xavier.x",
                first_name="Xavier",
                last_name="X",
            )
        with self.assertRaises(ValidationError):
            teach_without_first = User.objects.create(
                username="Xavier.x", last_name="X", email="xavier.x@mail.de"
            )

    def test_default_gropu_being_student(self):
        self.teach_without_specified_group = User.objects.create(
            username="user", first_name="userf", last_name="userl", email="userf@mail.de", password="pass"
        )

        self.assertEqual(self.teach_without_specified_group.groups.first().name, "Student")

    def test_email_unique(self):
        with self.assertRaises(IntegrityError):
            duplicate_user = (
                User.objects.create(
                    username="Xavier.x",
                    first_name="Xavier",
                    last_name="X",
                    email="xavier@mail.de",
                    phone_number="0176543999",
                ),
            )

    def test_complex(self):
        self.assertEqual(self.tut.date, timezone.now().date())
        self.assertEqual(self.tut.duration, 45)
        self.assertEqual(self.tut.subject.title, "Math")
        self.assertEqual(self.tut.teacher.username, "Xavier.x")

    def test_token_post_save(self):
        self.assertTrue(Token.objects.get(user=self.xavier))


class AuthenticationTestCase(TestCase):
    def setUp(self):
        self.stud = Group.objects.get(name="Student")
        self.teach = Group.objects.get(name="Teacher")

    def test_register_view(self):
        client = Client()

        # Test registration with valid data
        response = client.post(
            reverse("register"),
            {
                "username": "testuser",
                "first_name": "Test",
                "last_name": "User",
                "email": "testuser@example.com",
                "phone_number": "+123456789",
                "personal_teacher_code": "Amaru",
                "password": "testpassword",
                "confirmation": "testpassword",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.filter(username="testuser").count(), 1)  # check wether created

        # Test registration with invalid data (e.g., passwords don't match)
        response = client.post(
            reverse("register"),
            {
                "username": "testuser2",
                "first_name": "Test",
                "last_name": "User",
                "email": "testuser2@example.com",
                "phone_number": "+123456789",
                "personal_teacher_code": "Amaru",
                "password": "testpassword",
                "confirmation": "invalidpassword",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.filter(username="testuser").count(), 1)  # check that not created

    def test_login_view(self):
        client = Client()

        # Create a test user
        user = User.objects.create_user(
            username="testuser",
            password="testpassword",
            first_name="Xavier",
            last_name="X",
            email="xavier@mail.de",
            phone_number="0176543999",
        )

        # Test login with valid credentials
        response = client.post(reverse("login_view"), {"username": "testuser", "password": "testpassword"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Login successful")

        # Test login with invalid credentials
        response = client.post(reverse("login_view"), {"username": "testuser", "password": "wrongpassword"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid username and/or password.")