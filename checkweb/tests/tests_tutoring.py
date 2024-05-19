from django.test import TestCase, Client
from django.contrib.auth.models import Group
from django.utils import timezone
from ..models import User, Subject, Tutoring
import datetime
from django.urls import reverse
from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError
from rest_framework.authtoken.models import Token

class TutoringViewsTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.client = Client()

    def setUp(self):
        self.stud = Group.objects.get(name="Student")
        self.teach = Group.objects.get(name="Teacher")

        self.teacher = User.objects.create_user(
            "demo_teacher", "demo@mail.de", "password", first_name="demo", last_name="teacher"
        )
        self.teacher.groups.set([self.teach])
        self.teacher.save()

        self.student = User.objects.create(
            username="demo_student",
            first_name="demo",
            last_name="student",
            email="demo2@mail.de",
            password="password",
        )
        self.student.groups.set([self.stud])
        self.student.save()

        self.subject = Subject.objects.create(title="Astrologie")
        self.subject.save()

        self.tut = Tutoring.objects.create(
            date="2022-01-01",
            duration=45,
            subject=Subject.objects.create(title="TestSubject"),
            student=self.student,
            teacher=self.teacher,
            content="Ananas dies das.",
        )
        self.tut.save()

    def test_view_illegal(self):
        self.client.force_login(self.student)

        response = self.client.get(reverse)

    def test_create_legal(self):
        self.client.force_login(self.student)

        form_data = {
            "date": "1984-01-01",
            "duration": 45,
            "subject": self.subject.id,  # ID instead of Object!
            "teacher": self.teacher.id,
            "student": self.student.id,
            "content": "Demo tutoring session Lorem ipsum.",
        }

        # send POST to view
        response = self.client.post(reverse("checkweb:tutoring"), data=form_data)

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
        self.client.force_login(self.student)
        response = self.client.delete(reverse("checkweb:tutoring", args=[self.tut.id]))

        self.assertEqual(response.status_code, 403)
        self.assertTrue(
            Tutoring.objects.filter(id=self.tut.id).exists()
        )  # validate that not deleted

    def test_delete_legal(self):
        self.client.force_login(self.teacher)
        response = self.client.delete(reverse("checkweb:tutoring", args=[self.tut.id]))

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Tutoring.objects.filter(id=self.tut.id).exists())  # validate deletion

    def test_paid_status(self):
        # Case: in past => "pending"
        self.tut.date = datetime.date.today() - datetime.timedelta(days=32)
        self.assertEqual(self.tut.paid_status, "pending")

        # Case: in current month (today) => "future"
        self.tut.date = datetime.date.today()
        self.assertEqual(self.tut.paid_status, "future")

        # Case: paid => "paid"
        self.tut.paid = True
        self.assertEqual(self.tut.paid_status, "paid")
