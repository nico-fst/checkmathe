from django.test import TestCase
from django.utils import timezone
from .models import Role, User, Subject, Tutoring


class DB_Consistency(TestCase):
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
