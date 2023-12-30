from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Role, User, Subject, Tutoring
import datetime
from django.urls import reverse


class DB_ConsistencyTestCase(TestCase):
    def setUp(self):
        self.role = Role.objects.create(title="Student")
        now = timezone.now().date()
        self.tut = Tutoring.objects.create(
            date=now,
            duration=45,
            subject=Subject.objects.create(title="Math"),
            student=User.objects.create(
                username="Thore",
                phone_number="+49176999",
                preis_pro_45=20,
                role=Role.objects.create(title="Student"),
            ),
            teacher=User.objects.create(
                username="Xavier",
                phone_number="0176543999",
                role=Role.objects.create(title="Teacher"),
            ),
            content="labore culpa reprehenderit sit officia elit voluptate sit ad sit",
        )

    def test_creation(self):
        self.assertEqual(self.role.title, "Student")
        self.assertEqual(str(self.role), "Student")

    def test_choices(self):
        with self.assertRaises(ValueError):
            invalid_role = Role.objects.create(title="other")

    def test_complex(self):
        self.assertEqual(self.tut.date, timezone.now().date())
        self.assertEqual(self.tut.duration, 45)
        self.assertEqual(self.tut.subject.title, "Math")
        self.assertEqual(self.tut.teacher.username, "Xavier")


class TutoringViewsTestCase(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(username="demo_teacher", password="password")
        self.teacher.role = Role.objects.create(title="Teacher")
        self.teacher.save()

        self.student = User.objects.create_user(username="demo_student", password="password")
        self.student.role = Role.objects.create(title="Student")
        self.student.save()

        self.subject = Subject.objects.create(title="Astrologie")
        self.subject.save()

        self.tut = Tutoring.objects.create(
            date="2023-01-01",
            duration=45,
            subject=Subject.objects.create(title="TestSubject"),
            student=self.student,
            teacher=self.teacher,
            content="Ananas dies das.",
        )
        self.tut.save()

    def test_create_legal(self):
        client = Client()
        client.force_login(self.student)

        form_data = {
            "date": "1984-01-01",
            "duration": 45,
            "subject": self.tut.id,  # ID instead of Object!
            "teacher": self.teacher.id,
            "student": self.student.id,
            "content": "Demo tutoring session Lorem ipsum.",
        }

        # send POST to view
        response = client.post(reverse("tutoring"), data=form_data)

        self.assertEqual(response.status_code, 302)  # form submission successful?
        self.assertEqual(Tutoring.objects.count(), 2)  # new Tutoring object created?

        # Check if the Tutoring object has the correct attributes
        new_tut = Tutoring.objects.get(subject=Subject.objects.get(title="Astrologie"))

        self.assertEqual(new_tut.date, datetime.date(1984, 1, 1))
        self.assertEqual(new_tut.duration, 45)
        self.assertEqual(new_tut.teacher, self.teacher)
        self.assertEqual(new_tut.student, self.student)
        self.assertEqual(new_tut.content, "Demo tutoring session Lorem ipsum.")

    def test_delete_illegal(self):
        client = Client()
        client.force_login(self.student)
        response = client.post(reverse("delete_tut", args=[self.tut.id]))

        self.assertEqual(response.status_code, 403)
        self.assertTrue(Tutoring.objects.filter(id=self.tut.id).exists())  # validate that not deleted

    def test_delete_legal(self):
        client = Client()
        client.force_login(self.teacher)
        response = client.post(reverse("delete_tut", args=[self.tut.id]))

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Tutoring.objects.filter(id=self.tut.id).exists())  # validate deletion
