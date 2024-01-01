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
        self.xavier = User.objects.create_user(
            "xavier.x", "xavier.x@mail.de", "password", first_name="Xavier", last_name="X"
        )
        self.nico.groups.set([self.teach])
        self.kat = User.objects.create_user(
            "kat.ev", "kat.ev@web.de", "password", first_name="Katniss", last_name="Everdeen"
        )

        resp_token = self.client.post(reverse("obtain_auth_token"), {"username": "nico.st", "password": "password"})
        self.token_nico = resp_token.json().get("token")

        resp_token = self.client.post(reverse("obtain_auth_token"), {"username": "kat.ev", "password": "password"})
        self.token_kat = resp_token.json().get("token")

        self.tut = Tutoring.objects.create(
            date=timezone.now().date(),
            duration=45,
            subject=Subject.objects.create(title="Math"),
            student=self.kat,
            teacher=self.nico,
            content="labore culpa reprehenderit sit officia elit voluptate sit ad sit",
        )

    def test_get_subjects(self):
        response = self.client.get(reverse("get_subjects"))
        self.assertEqual(response.status_code, 200)

    def test_add_subject(self):
        response = self.client.post(reverse("add_subject"), self.subject_data, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Subject.objects.all().count(), 2)

    def test_subject_serialization(self):
        subject = Subject.objects.create(title="Test Subject")
        serializer = SubjectSerializer(subject)
        self.assertEqual(serializer.data, {"id": 2, "title": "Test Subject"})

    def test_user_list_view_unauthorized(self):
        response = self.client.get(reverse("user_list_view"))
        self.assertEqual(response.status_code, 401)

    def test_obtain_auth_token(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token_nico}")  # legal as authorized nico
        resp_usernames_authorized = self.client.get(reverse("user_list_view"))

        self.client.credentials(HTTP_AUTHORIZATION=f"Token wrongtoken")
        resp_usernames_wront_token = self.client.get(reverse("user_list_view"))

        # TEST authorized: fetched
        self.assertEqual(resp_usernames_authorized.status_code, 200)
        self.assertIn("nico.st", json.dumps(resp_usernames_authorized.json()))

        # TEST wrong token: unauthorized resp. wrong token
        self.assertEqual(resp_usernames_wront_token.status_code, 401)

    def test_get_tutoring(self):
        # legal since nico is teacher
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token_nico}")
        resp_authorized = self.client.get(reverse("tutoring_view", kwargs={"tut_id": 1}))

        # illegal since wrong token
        self.client.credentials(HTTP_AUTHORIZATION=f"Token wrongtoken")
        resp_wrong_token = self.client.get(reverse("tutoring_view", kwargs={"tut_id": 1}))

        # TEST authorized: fetched
        self.assertEqual(resp_authorized.status_code, 200)  # check if successful
        self.assertEqual(resp_authorized.json().get("student"), self.kat.serialize())  # check if right tut

        # TEST wrong token: unauthorized
        self.assertEqual(resp_wrong_token.status_code, 401)

    def test_delete_tutoring(self):
        # illegal since kat is not teacher of tut
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token_kat}")
        resp_as_student = self.client.delete(reverse("tutoring_view", kwargs={"tut_id": 1}))

        # TEST as student: not deleted
        self.assertEqual(resp_as_student.status_code, 403)  # forbidden
        self.assertEqual(Tutoring.objects.all().count(), 1)  # still 1 Tutoring

        # legal since nico is teacher of tut
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token_nico}")
        resp_as_teacher = self.client.delete(reverse("tutoring_view", kwargs={"tut_id": 1}))

        # TEST legal: deleted
        self.assertEqual(resp_as_teacher.status_code, 200)
        self.assertEqual(Tutoring.objects.all().count(), 0)  # after deletion no Tutoring left
