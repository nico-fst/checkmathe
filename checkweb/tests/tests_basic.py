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