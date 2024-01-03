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


class ChangePaidPerMonthTests(TestCase):
    def setUp(self):
        self.math = Subject.objects.create(title="Math")
        self.teach = Group.objects.get(name="Teacher")
        self.url = reverse("api:create_tutoring")

        self.nico = User.objects.create_user(
            "nico.st", "nico.st@mail.de", "password", first_name="Nico", last_name="St"
        )
        self.nico.groups.set([self.teach])

        self.xavier = User.objects.create_user(
            "xavier.x", "xavier.x@mail.de", "password", first_name="Xavier", last_name="X"
        )
        self.xavier.groups.set([self.teach])

        self.kat = User.objects.create_user(
            "kat.ev",
            "kat.ev@web.de",
            "password",
            first_name="Katniss",
            last_name="Everdeen",
        )

        self.tutoring_nico1 = Tutoring.objects.create(
            date="2022-01-01",
            duration=45,
            subject=self.math,
            student=self.kat,
            teacher=self.nico,
            content="Lorem ipsum",
        )
        self.tutoring_nico2 = Tutoring.objects.create(
            date="2022-01-02",
            duration=30,
            subject=self.math,
            student=self.kat,
            teacher=self.nico,
            content="Ananas",
        )
        self.tutoring_xavier = Tutoring.objects.create(
            date="2022-01-02",
            duration=30,
            subject=self.math,
            student=self.kat,
            teacher=self.xavier,
            content="Ananas",
        )

        self.client = APIClient()
        self.client.force_authenticate(user=self.nico)

    def test_paid_default_false(self):
        self.assertEqual(self.tutoring_nico1.paid, False)
        self.assertEqual(self.tutoring_nico2.paid, False)
        self.assertEqual(self.tutoring_xavier.paid, False)

    def test_paid(self):
        resp_paid_missing = self.client.post(
            reverse("api:change_paid_per_month"),
            {"student_username": "kat.ev", "year": 2022, "month": 1},
            format="json",
        )

        # TEST paid msising: not changed
        self.assertEqual(resp_paid_missing.status_code, status.HTTP_400_BAD_REQUEST)
        tuts_nico = Tutoring.objects.filter(teacher=self.nico)
        for tut in tuts_nico:
            self.assertEqual(tut.paid, False)
        self.assertEqual(Tutoring.objects.get(teacher=self.xavier).paid, False)

        resp_paid_invalid = self.client.post(
            reverse("api:change_paid_per_month"),
            {"student_username": "kat.ev", "year": 2022, "month": 1, "paid": "INVALID"},
            format="json",
        )

        # TEST paid invalid: not changed
        self.assertEqual(resp_paid_invalid.status_code, status.HTTP_400_BAD_REQUEST)
        tuts_nico = Tutoring.objects.filter(teacher=self.nico)
        for tut in tuts_nico:
            self.assertEqual(tut.paid, False)
        self.assertEqual(Tutoring.objects.get(teacher=self.xavier).paid, False)

        resp_paid_true = self.client.post(
            reverse("api:change_paid_per_month"),
            {"student_username": "kat.ev", "year": 2022, "month": 1, "paid": True},
            format="json",
        )

        # TEST paid true: all tuts of nico changed to true, xavier not touched
        self.assertEqual(resp_paid_true.status_code, status.HTTP_200_OK)
        tuts_nico = Tutoring.objects.filter(teacher=self.nico)
        for tut in tuts_nico:
            self.assertEqual(tut.paid, True)
        self.assertEqual(Tutoring.objects.get(teacher=self.xavier).paid, False)

    def test_student_username(self):
        resp_username_missing = self.client.post(
            reverse("api:change_paid_per_month"),
            {"year": 2022, "month": 1, "paid": True},
            format="json",
        )

        # TEST username missing: not changed
        self.assertEqual(resp_username_missing.status_code, status.HTTP_400_BAD_REQUEST)
        tuts_nico = Tutoring.objects.filter(teacher=self.nico)
        for tut in tuts_nico:
            self.assertEqual(tut.paid, False)
        self.assertEqual(Tutoring.objects.get(teacher=self.xavier).paid, False)

        resp_username_not_existing = self.client.post(
            reverse("api:change_paid_per_month"),
            {"NOTEXISTING": "kat.ev", "year": 2022, "month": 1, "paid": False},
            format="json",
        )

        # TEST username not existing: not changed
        self.assertEqual(resp_username_not_existing.status_code, status.HTTP_400_BAD_REQUEST)
        tuts_nico = Tutoring.objects.filter(teacher=self.nico)
        for tut in tuts_nico:
            self.assertEqual(tut.paid, False)
        self.assertEqual(Tutoring.objects.get(teacher=self.xavier).paid, False)

    def test_year_month(self):
        resp_year_missing = self.client.post(
            reverse("api:change_paid_per_month"),
            {"student_username": "kat.ev", "month": 1, "paid": True},
            format="json",
        )

        # TEST year missing: not changed
        self.assertEqual(resp_year_missing.status_code, status.HTTP_400_BAD_REQUEST)
        tuts_nico = Tutoring.objects.filter(teacher=self.nico)
        for tut in tuts_nico:
            self.assertEqual(tut.paid, False)
        self.assertEqual(Tutoring.objects.get(teacher=self.xavier).paid, False)

        resp_month_missing = self.client.post(
            reverse("api:change_paid_per_month"),
            {"student_username": "kat.ev", "year": 2023, "paid": True},
            format="json",
        )

        # TEST month missing: not changed
        self.assertEqual(resp_month_missing.status_code, status.HTTP_400_BAD_REQUEST)
        tuts_nico = Tutoring.objects.filter(teacher=self.nico)
        for tut in tuts_nico:
            self.assertEqual(tut.paid, False)
        self.assertEqual(Tutoring.objects.get(teacher=self.xavier).paid, False)
