from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from checkweb.models import Subject, Tutoring, User
from .serializers import SubjectSerializer
import json


class SimpleRequestsTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.subject_data = {"title": "Test Subject"}

        User.objects.create_user("nico.st", "nico.st@mail.de", "password", first_name="Nico", last_name="St")

    def test_get_subject(self):
        response = self.client.get(reverse("getSubject"))
        self.assertEqual(response.status_code, 200)

    def test_add_subject(self):
        response = self.client.post(reverse("addSubject"), self.subject_data, format="json")
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
        resp_token = self.client.post(reverse("obtain_auth_token"), {"username": "nico.st", "password": "password"})
        token = resp_token.json().get("token")
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token}")
        resp_usernames = self.client.get(reverse("user_list_view"))

        self.assertEqual(resp_token.status_code, 200)
        self.assertEqual(resp_usernames.status_code, 200)
        self.assertIn("token", json.dumps(resp_token.json()))
        self.assertIn("nico.st", json.dumps(resp_usernames.json()))
