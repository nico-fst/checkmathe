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
        self.nico.groups.set([self.teach])
        self.kat = User.objects.create_user(
            "kat.ev", "kat.ev@web.de", "password", first_name="Katniss", last_name="Everdeen"
        )
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
        resp_token = self.client.post(reverse("obtain_auth_token"), {"username": "nico.st", "password": "password"})
        self.token = resp_token.json().get("token")
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token}")
        resp_usernames = self.client.get(reverse("user_list_view"))

        self.assertEqual(resp_token.status_code, 200)
        self.assertEqual(resp_usernames.status_code, 200)
        self.assertIn("token", json.dumps(resp_token.json()))
        self.assertIn("nico.st", json.dumps(resp_usernames.json()))

    def test_get_tutoring(self):
        # get token
        resp_token = self.client.post(reverse("obtain_auth_token"), {"username": "nico.st", "password": "password"})
        self.token = resp_token.json().get("token")
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token}")

        # actually get tutoring
        response = self.client.get(reverse("tutoring_view", kwargs={"tut_id": 1}))
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token}")

        self.assertEqual(response.status_code, 200)  # check if successful
        self.assertEqual(response.json().get("student"), self.kat.serialize())  # check if right tut