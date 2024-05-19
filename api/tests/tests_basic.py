from rest_framework import status
from rest_framework.test import APIClient

from django.contrib.auth.models import Group
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

import os
import json

from checkweb.models import Subject, Tutoring, User
from checkweb.views.views_basic import calc_stundenkosten
from ..serializers import SubjectSerializer


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
        response = self.client.get(reverse("api:subject"))
        self.assertEqual(response.status_code, 200)

    def test_add_subject(self):
        self.n_subjects = Subject.objects.all().count()
        response = self.client.post(reverse("api:subject"), self.subject_data, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Subject.objects.all().count(), self.n_subjects + 1)

    def test_subject_serialization(self):
        subject = Subject.objects.create(title="Test Subject")
        serializer = SubjectSerializer(subject)
        values = [value for key, value in serializer.data.items()]  # ©esplittet, weil die f nicht mit {}s umgehen kann bruh
        self.assertIn("Test Subject", values)

    def test_user_list_unauthorized(self):
        response = self.client.get(reverse("api:user"))
        self.assertEqual(response.status_code, 401)

    def test_obtain_auth_token(self):
        self.nico.groups.set([Group.objects.get(name="Teacher")])
        resp_token = self.client.post(
            reverse("api:obtain_auth_token"), {"username": "nico.st", "password": "password"}
        )
        self.token_nico = resp_token.json().get("token")

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.token_nico}"
        )  # legal as authorized nico
        resp_usernames_authorized = self.client.get(reverse("api:user"))

        self.client.credentials(HTTP_AUTHORIZATION=f"Token wrongtoken")
        resp_usernames_wrong_token = self.client.get(reverse("api:user"))

        # TEST authorized: fetched
        self.assertEqual(resp_usernames_authorized.status_code, 200)
        self.assertIn("nico.st", json.dumps(resp_usernames_authorized.json()))

        # TEST wrong token: unauthorized resp. wrong token
        self.assertEqual(resp_usernames_wrong_token.status_code, 401)


class SumViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.math = Subject.objects.get(title="Math")
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

    def test_sum_authenticated_teacher(self):
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
        response = self.client.get(reverse("api:sum", args=("kat.ev", 2022, 1)))

        # TEST 404 if prop preis_pro_45 empty
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        self.kat.preis_pro_45 = 15
        self.kat.save()
        response = self.client.get(reverse("api:sum", args=("kat.ev", 2022, 1)))

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

    def test_sum_authenticated_student(self):
        self.client.force_authenticate(user=self.kat)

        self.kat.preis_pro_45 = 15
        self.kat.save()

        # legal as participating student
        response = self.client.get(reverse("api:sum", args=("kat.ev", 2022, 1)))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # illegal as not participating student
        response = self.client.get(reverse("api:sum", args=("nico.st", 2022, 1)))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_sum_unauthenticated(self):
        response = self.client.get(reverse("api:sum", args=("kat.ev", 2022, 1)))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
