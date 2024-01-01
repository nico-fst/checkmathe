from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import Group
from rest_framework import status
from django.utils import timezone
from rest_framework.test import APIClient
from checkweb.models import Subject, Tutoring, User
from .serializers import SubjectSerializer
import json


class SimpleRequestsTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.subject_data = {"title": "Test Subject"}
        self.teach = Group.objects.get(name="Teacher")
        self.token = None

        self.nico = User.objects.create_user(
            "nico.st", "nico.st@mail.de", "password", first_name="Nico", last_name="St"
        )

    def test_get_subjects(self):
        response = self.client.get(reverse("get_subjects"))
        self.assertEqual(response.status_code, 200)

    def test_add_subject(self):
        response = self.client.post(reverse("add_subject"), self.subject_data, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Subject.objects.all().count(), 1)

    def test_subject_serialization(self):
        subject = Subject.objects.create(title="Test Subject")
        serializer = SubjectSerializer(subject)
        self.assertEqual(serializer.data, {"id": 1, "title": "Test Subject"})

    def test_user_list_view_unauthorized(self):
        response = self.client.get(reverse("user_list_view"))
        self.assertEqual(response.status_code, 401)

    def test_obtain_auth_token(self):
        resp_token = self.client.post(
            reverse("obtain_auth_token"), {"username": "nico.st", "password": "password"}
        )
        self.token_nico = resp_token.json().get("token")

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.token_nico}"
        )  # legal as authorized nico
        resp_usernames_authorized = self.client.get(reverse("user_list_view"))

        self.client.credentials(HTTP_AUTHORIZATION=f"Token wrongtoken")
        resp_usernames_wront_token = self.client.get(reverse("user_list_view"))

        # TEST authorized: fetched
        self.assertEqual(resp_usernames_authorized.status_code, 200)
        self.assertIn("nico.st", json.dumps(resp_usernames_authorized.json()))

        # TEST wrong token: unauthorized resp. wrong token
        self.assertEqual(resp_usernames_wront_token.status_code, 401)


class TutoringTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.subject_data = {"title": "Test Subject"}
        self.teach = Group.objects.get(name="Teacher")
        self.token = None
        self.url_tut_1 = reverse("tutoring_view", kwargs={"tut_id": 1})

        self.nico = User.objects.create_user(
            "nico.st", "nico.st@mail.de", "password", first_name="Nico", last_name="St"
        )
        self.nico.groups.set([self.teach])
        resp_token = self.client.post(
            reverse("obtain_auth_token"), {"username": "nico.st", "password": "password"}
        )
        self.token_nico = resp_token.json().get("token")

        self.xavier = User.objects.create_user(
            "xavier.x", "xavier.x@mail.de", "password", first_name="Xavier", last_name="X"
        )
        self.xavier.groups.set([self.teach])
        resp_token = self.client.post(
            reverse("obtain_auth_token"), {"username": "xavier.x", "password": "password"}
        )
        self.token_xavier = resp_token.json().get("token")

        self.kat = User.objects.create_user(
            "kat.ev",
            "kat.ev@web.de",
            "password",
            first_name="Katniss",
            last_name="Everdeen",
        )
        resp_token = self.client.post(
            reverse("obtain_auth_token"), {"username": "kat.ev", "password": "password"}
        )
        self.token_kat = resp_token.json().get("token")

        self.tut = Tutoring.objects.create(
            date=timezone.now().date(),
            duration=45,
            subject=Subject.objects.create(title="Math"),
            student=self.kat,
            teacher=self.nico,
            content="Lorem ipsum",
        )

    def test_get_tutoring(self):
        # legal since nico is teacher
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token_nico}")
        resp_authorized = self.client.get(self.url_tut_1)

        # illegal since wrong token
        self.client.credentials(HTTP_AUTHORIZATION=f"Token wrongtoken")
        resp_wrong_token = self.client.get(self.url_tut_1)

        # TEST authorized: fetched
        self.assertEqual(resp_authorized.status_code, 200)  # check if successful
        self.assertEqual(
            resp_authorized.json().get("student"), self.kat.serialize()
        )  # check if right tut

        # TEST wrong token: unauthorized
        self.assertEqual(resp_wrong_token.status_code, 401)

    def test_delete_tutoring(self):
        # illegal since kat is not teacher of tut
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token_kat}")
        resp_as_student = self.client.delete(self.url_tut_1)

        # TEST as student: not deleted
        self.assertEqual(resp_as_student.status_code, 403)  # forbidden
        self.assertEqual(Tutoring.objects.all().count(), 1)  # still 1 Tutoring

        # illegal since xavier is not teacher of this tut
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token_xavier}")
        resp_as_wrong_teacher = self.client.delete(self.url_tut_1)

        # TEST wrong teacher: not deleted
        self.assertEqual(resp_as_wrong_teacher.status_code, 403)  # forbidden
        self.assertEqual(Tutoring.objects.all().count(), 1)  # still 1 Tutoring

        # legal since nico is teacher of tut
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token_nico}")
        resp_as_teacher = self.client.delete(self.url_tut_1)

        # TEST legal: deleted
        self.assertEqual(resp_as_teacher.status_code, 200)
        self.assertEqual(Tutoring.objects.all().count(), 0)  # after deletion no Tutoring left

    def test_put_tutoring(self):
        # illegal since xavier is not teacher of this tut
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token_xavier}")
        resp_as_wrong_teacher = self.client.put(self.url_tut_1)

        # TEST as wrong teacher: not put
        self.assertEqual(resp_as_wrong_teacher.status_code, 403)  # forbidden
        self.assertEqual(self.tut.content, "Lorem ipsum")  # Content not changed

        # legal since nico is teacher of this tut
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token_nico}")
        resp_as_own_teacher = self.client.put(
            self.url_tut_1,
            {"new_values": {"content": "New Content. Ananas."}},
            format="json",
        )

        # TEST as own teacher: put (changed content)
        self.assertEqual(resp_as_own_teacher.status_code, 200)
        self.assertEqual(Tutoring.objects.get(id=1).content, "New Content. Ananas.")


class CreateTutoringViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.math = Subject.objects.create(title="Math")
        self.teach = Group.objects.get(name="Teacher")
        self.token = None
        self.url = reverse("create_tutoring")

        self.nico = User.objects.create_user(
            "nico.st", "nico.st@mail.de", "password", first_name="Nico", last_name="St"
        )
        self.nico.groups.set([self.teach])
        resp_token = self.client.post(
            reverse("obtain_auth_token"), {"username": "nico.st", "password": "password"}
        )
        self.token_nico = resp_token.json().get("token")

        self.xavier = User.objects.create_user(
            "xavier.x", "xavier.x@mail.de", "password", first_name="Xavier", last_name="X"
        )
        self.xavier.groups.set([self.teach])
        resp_token = self.client.post(
            reverse("obtain_auth_token"), {"username": "xavier.x", "password": "password"}
        )
        self.token_xavier = resp_token.json().get("token")

        self.kat = User.objects.create_user(
            "kat.ev",
            "kat.ev@web.de",
            "password",
            first_name="Katniss",
            last_name="Everdeen",
        )
        resp_token = self.client.post(
            reverse("obtain_auth_token"), {"username": "kat.ev", "password": "password"}
        )
        self.token_kat = resp_token.json().get("token")

    def test_create_tutoring_successful(self):
        data = {
            "YYYY-MM-DD": "2020-12-01",
            "duration_in_min": 45,
            "subject_title": "Math",
            "teacher_username": "nico.st",
            "student_username": "kat.ev",
            "content": "Sinussatz",
        }

        # log in and send
        self.client.force_authenticate(user=self.nico)
        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Tutoring.objects.count(), 1)
        self.assertEqual(Tutoring.objects.first().teacher, self.nico)
        self.assertEqual(Tutoring.objects.first().student, self.kat)

    def test_create_tutoring_permission_denied(self):
        data = {
            "YYYY-MM-DD": "2020-12-01",
            "duration_in_min": 45,
            "subject_title": "Math",
            "teacher_username": "nico.st",
            "student_username": "kat.ev",
            "content": "Sinussatz",
        }

        # No authentication
        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_tutoring_duplicate(self):
        # Create an existing tutoring session
        Tutoring.objects.create(
            date="2020-12-01",
            duration=45,
            subject=self.math,
            teacher=self.nico,
            student=self.kat,
            content="Sinussatz",
        )

        data = {
            "YYYY-MM-DD": "2020-12-01",
            "duration_in_min": 45,
            "subject_title": "Math",
            "teacher_username": "nico.st",
            "student_username": "kat.ev",
            "content": "Sinussatz",
        }

        self.client.force_authenticate(user=self.nico)
        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_tutoring_guard_username_not_exist(self):
        # Attempt to create a tutoring session with a non-existent teacher username
        self.client.force_authenticate(user=self.nico)
        response = self.client.post(
            reverse("create_tutoring"),
            {
                "subject_title": "Math",
                "teacher_username": "nonexistent_teacher",
                "student_username": "kat.ev",
            },
            format="json",
        )

        # Test: Not Found
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(
            Tutoring.objects.all().count(), 0
        )  # Tutoring session should not be created

    def test_create_tutoring_guard_user_not_in_correct_role(self):
        # Attempt to create a tutoring session with a student as a teacher
        self.client.force_authenticate(user=self.nico)
        response = self.client.post(
            reverse("create_tutoring"),
            {
                "subject_title": "Math",
                "teacher_username": "kat.ev",
                "student_username": "kat.ev",
            },
            format="json",
        )

        # Test: Forbidden
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            Tutoring.objects.all().count(), 0
        )  # Tutoring session should not be created

    def test_create_tutoring_guard_date_format_invalid(self):
        # Attempt to create a tutoring session with an invalid date format
        self.client.force_authenticate(user=self.nico)
        response = self.client.post(
            reverse("create_tutoring"),
            {
                "subject_title": "Math",
                "teacher_username": "nico.st",
                "student_username": "kat.ev",
                "YYYY-MM-DD": "invalid_date_format",
            },
            format="json",
        )

        # Test: Forbidden
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            Tutoring.objects.all().count(), 0
        )  # Tutoring session should not be created

    def test_create_tutoring_guard_duration_out_of_range(self):
        # Attempt to create a tutoring session with an invalid duration (out of range)
        self.client.force_authenticate(user=self.nico)
        response = self.client.post(
            reverse("create_tutoring"),
            {
                "subject_title": "Math",
                "teacher_username": "nico.st",
                "student_username": "kat.ev",
                "YYYY-MM-DD": "2022-01-01",
                "duration_in_min": 400,
            },
            format="json",
        )

        # Test: Forbidden
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            Tutoring.objects.all().count(), 0
        )  # Tutoring session should not be created

    def test_create_tutoring_guard_content_empty(self):
        # Attempt to create a tutoring session with empty content
        self.client.force_authenticate(user=self.nico)
        response = self.client.post(
            reverse("create_tutoring"),
            {
                "subject_title": "Math",
                "teacher_username": "nico.st",
                "student_username": "kat.ev",
                "YYYY-MM-DD": "2022-01-01",
                "duration_in_min": 60,
                "content": "",
            },
            format="json",
        )

        # Test: Forbidden
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            Tutoring.objects.all().count(), 0
        )  # Tutoring session should not be created

    def test_create_tutoring_guard_duplicate_tutoring(self):
        # Create an existing tutoring session
        Tutoring.objects.create(
            date="2022-01-01",
            duration=60,
            subject=self.math,
            teacher=self.nico,
            student=self.kat,
            content="Sinussatz",
        )

        # Attempt to create a duplicate tutoring session
        self.client.force_authenticate(user=self.nico)
        response = self.client.post(
            reverse("create_tutoring"),
            {
                "subject_title": "Math",
                "teacher_username": "nico.st",
                "student_username": "kat.ev",
                "YYYY-MM-DD": "2022-01-01",
                "duration_in_min": 60,
                "content": "Sinussatz",
            },
            format="json",
        )

        # Test: Forbidden
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            Tutoring.objects.all().count(), 1
        )  # Tutoring session should not be created


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
        response = self.client.get(reverse("user_view", kwargs={"user_id": self.student_user.id}))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_nonexistent_user(self):
        self.client.force_authenticate(user=self.teacher_user)
        response = self.client.get(reverse("user_view", kwargs={"user_id": 999}))
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
        response = self.client.post(reverse("user_view"), data, format="json")
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
        response = self.client.post(reverse("user_view"), data, format="json")
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
            reverse("delete_user", kwargs={"username": self.student_user.username})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_nonexistent_user(self):
        self.client.force_authenticate(user=self.teacher_user)
        response = self.client.delete(
            reverse("delete_user", kwargs={"username": "nonexistent_user"})
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_student_cannot_delete_other_student(self):
        self.client.force_authenticate(user=self.student_user)
        response = self.client.delete(
            reverse("delete_user", kwargs={"username": self.teacher_user.username})
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_student_can_delete_self(self):
        self.client.force_authenticate(user=self.student_user)
        response = self.client.delete(
            reverse("delete_user", kwargs={"username": self.student_user.username})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
