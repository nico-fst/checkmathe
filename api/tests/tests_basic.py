from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import Group
from rest_framework import status
from django.utils import timezone
from rest_framework.test import APIClient
from checkweb.models import Subject, Tutoring, User
from ..serializers import SubjectSerializer
from checkweb.views import calc_stundenkosten
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
        response = self.client.get(reverse("api:get_subjects"))
        self.assertEqual(response.status_code, 200)

    def test_add_subject(self):
        response = self.client.post(reverse("api:add_subject"), self.subject_data, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Subject.objects.all().count(), 1)

    def test_subject_serialization(self):
        subject = Subject.objects.create(title="Test Subject")
        serializer = SubjectSerializer(subject)
        self.assertEqual(serializer.data, {"id": 1, "title": "Test Subject"})

    def test_user_list_view_unauthorized(self):
        response = self.client.get(reverse("api:user_list_view"))
        self.assertEqual(response.status_code, 401)

    def test_obtain_auth_token(self):
        resp_token = self.client.post(
            reverse("api:obtain_auth_token"), {"username": "nico.st", "password": "password"}
        )
        self.token_nico = resp_token.json().get("token")

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.token_nico}"
        )  # legal as authorized nico
        resp_usernames_authorized = self.client.get(reverse("api:user_list_view"))

        self.client.credentials(HTTP_AUTHORIZATION=f"Token wrongtoken")
        resp_usernames_wront_token = self.client.get(reverse("api:user_list_view"))

        # TEST authorized: fetched
        self.assertEqual(resp_usernames_authorized.status_code, 200)
        self.assertIn("nico.st", json.dumps(resp_usernames_authorized.json()))

        # TEST wrong token: unauthorized resp. wrong token
        self.assertEqual(resp_usernames_wront_token.status_code, 401)


class SumViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.math = Subject.objects.create(title="Math")
        self.teach = Group.objects.get(name="Teacher")

        self.nico = User.objects.create_user(
            "nico.st", "nico.st@mail.de", "password", first_name="Nico", last_name="St"
        )
        self.nico.groups.set([self.teach])

        self.kat = User.objects.create_user(
            "kat.ev",
            "kat.ev@web.de",
            "password",
            first_name="Katniss",
            last_name="Everdeen",
        )

    def test_sum_view_authenticated_teacher(self):
        tutoring1 = Tutoring.objects.create(
            date="2022-01-01",
            duration=45,
            subject=self.math,
            student=self.kat,
            teacher=self.nico,
            content="Lorem ipsum",
        )
        tutoring2 = Tutoring.objects.create(
            date="2022-01-02",
            duration=30,
            subject=self.math,
            student=self.kat,
            teacher=self.nico,
            content="Ananas",
        )

        self.client.force_authenticate(user=self.nico)
        response = self.client.get(reverse("api:sum_view", args=("kat.ev", 2022, 1)))

        # TEST 404 if prop preis_pro_45 empty
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        self.kat.preis_pro_45 = 15
        self.kat.save()
        response = self.client.get(reverse("api:sum_view", args=("kat.ev", 2022, 1)))

        # TEST 200 if prop exists
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        expected_sum = calc_stundenkosten(self.kat, tutoring1) + calc_stundenkosten(
            self.kat, tutoring2
        )
        expected_data = {
            "sum": expected_sum,
            "count_tutorings": 2,
            "tutorings": [tutoring1.serialize(), tutoring2.serialize()],
        }

        self.assertEqual(expected_sum, response.data.get("sum"))
        self.assertEqual(2, response.data.get("count_tutorings"))

    def test_sum_view_authenticated_student(self):
        self.client.force_authenticate(user=self.kat)

        self.kat.preis_pro_45 = 15
        self.kat.save()

        # legal as participating student
        response = self.client.get(reverse("api:sum_view", args=("kat.ev", 2022, 1)))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # illegal as not participating student
        response = self.client.get(reverse("api:sum_view", args=("nico.st", 2022, 1)))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_sum_view_unauthenticated(self):
        response = self.client.get(reverse("api:sum_view", args=("kat.ev", 2022, 1)))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
