from rest_framework import status
from rest_framework.test import APIClient

from django.contrib.auth.models import Group
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse, NoReverseMatch
from django.utils import timezone

import os
import json

from checkweb.models import Subject, Tutoring, User
from ..serializers import SubjectSerializer


class TutsPerMonthTests(TestCase):
    def setUp(self):
        self.math = Subject.objects.get(title="Math")
        self.teach = Group.objects.get(name="Teacher")
        self.url = reverse("api:tutoring")

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
            preis_pro_45=45
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
        self.tutoring_nico_future = Tutoring.objects.create(
            date="2022-02-02",
            duration=30,
            subject=self.math,
            student=self.kat,
            teacher=self.nico,
            content="Erst in der Zukunft",
        )
        self.tutoring_xavier = Tutoring.objects.create(
            date="2022-01-02",
            duration=30,
            subject=self.math,
            student=self.kat,
            teacher=self.xavier,
            content="Die das",
        )

        self.client = APIClient()
        self.client.force_authenticate(user=self.nico)

    def test_post_paid_default_false(self):
        self.assertEqual(self.tutoring_nico1.paid, False)
        self.assertEqual(self.tutoring_nico2.paid, False)
        self.assertEqual(self.tutoring_xavier.paid, False)

    def test_post_paid(self):
        resp_paid_missing = self.client.post(
            reverse("api:tuts_per_month", kwargs={"student_username": "kat.ev"}),
            {"year": 2022, "month": 1},
            format="json",
        )

        # TEST paid msising: not changed
        self.assertEqual(resp_paid_missing.status_code, status.HTTP_400_BAD_REQUEST)
        tuts_nico = Tutoring.objects.filter(teacher=self.nico)
        for tut in tuts_nico:
            self.assertEqual(tut.paid, False)
        self.assertEqual(Tutoring.objects.get(teacher=self.xavier).paid, False)

        resp_paid_invalid = self.client.post(
            reverse("api:tuts_per_month", kwargs={"student_username": "kat.ev"}),
            {"year": 2022, "month": 1, "paid": "INVALID"},
            format="json",
        )

        # TEST paid invalid: not changed
        self.assertEqual(resp_paid_invalid.status_code, status.HTTP_400_BAD_REQUEST)
        tuts_nico = Tutoring.objects.filter(teacher=self.nico)
        for tut in tuts_nico:
            self.assertEqual(tut.paid, False)
        self.assertEqual(Tutoring.objects.get(teacher=self.xavier).paid, False)

        resp_paid_true = self.client.post(
            reverse("api:tuts_per_month", kwargs={"student_username": "kat.ev"}),
            {"year": 2022, "month": 1, "paid": True},
            format="json",
        )

        # TEST paid true: all tuts of nico changed to true, xavier not touched
        self.assertEqual(resp_paid_true.status_code, status.HTTP_200_OK)
        tuts_nico = Tutoring.objects.filter(teacher=self.nico, date__year=2022, date__month=1)
        for tut in tuts_nico:
            self.assertEqual(tut.paid, True)
        self.assertEqual(Tutoring.objects.get(teacher=self.xavier).paid, False)

    def test_post_student_username(self):
        with self.assertRaises(NoReverseMatch):
            resp_username_missing = self.client.post(
                reverse("api:tuts_per_month", kwargs={"student_username": ""}),
                {"year": 2022, "month": 1, "paid": True},
                format="json",
            )

        # TEST username missing: not changed
        tuts_nico = Tutoring.objects.filter(teacher=self.nico)
        for tut in tuts_nico:
            self.assertEqual(tut.paid, False)
        self.assertEqual(Tutoring.objects.get(teacher=self.xavier).paid, False)

        with self.assertRaises(NoReverseMatch):
            resp_username_not_existing = self.client.post(
                reverse("api:tuts_per_month", kwargs={"NOTEXISTING": "kat.ev"}),
                {"year": 2022, "month": 1, "paid": False},
                format="json",
            )

        # TEST username not existing: not changed
        tuts_nico = Tutoring.objects.filter(teacher=self.nico)
        for tut in tuts_nico:
            self.assertEqual(tut.paid, False)
        self.assertEqual(Tutoring.objects.get(teacher=self.xavier).paid, False)

    def test_post_year_month(self):
        resp_year_missing = self.client.post(
            reverse("api:tuts_per_month", kwargs={"student_username": "kat.ev"}),
            {"month": 1, "paid": True},
            format="json",
        )

        # TEST year missing: not changed
        self.assertEqual(resp_year_missing.status_code, status.HTTP_400_BAD_REQUEST)
        tuts_nico = Tutoring.objects.filter(teacher=self.nico)
        for tut in tuts_nico:
            self.assertEqual(tut.paid, False)
        self.assertEqual(Tutoring.objects.get(teacher=self.xavier).paid, False)

        resp_month_missing = self.client.post(
            reverse("api:tuts_per_month", kwargs={"student_username": "kat.ev"}),
            {"year": 2023, "paid": True},
            format="json",
        )

        # TEST month missing: not changed
        self.assertEqual(resp_month_missing.status_code, status.HTTP_400_BAD_REQUEST)
        tuts_nico = Tutoring.objects.filter(teacher=self.nico)
        for tut in tuts_nico:
            self.assertEqual(tut.paid, False)
        self.assertEqual(Tutoring.objects.get(teacher=self.xavier).paid, False)

    def test_get(self):
        resp_all_unpaid = self.client.get(
            reverse(
                "api:tuts_per_month",
                kwargs={
                    "student_username": "kat.ev",
                    "year": 2022,
                    "month": 1,
                },
            ),
        )

        # TEST all unpaid
        self.assertEqual(resp_all_unpaid.status_code, status.HTTP_200_OK)
        self.assertEqual(resp_all_unpaid.json().get("is_paid"), False)
        self.assertEqual(resp_all_unpaid.json().get("tuts_paid"), [])
        self.assertEqual(len(resp_all_unpaid.json().get("tuts_unpaid")), 3)

        # Now one of the two Tutorings is paid
        self.tutoring_nico1.paid = True
        self.tutoring_nico1.save()

        resp_one_paid = self.client.get(
            reverse(
                "api:tuts_per_month",
                kwargs={
                    "student_username": "kat.ev",
                    "year": 2022,
                    "month": 1,
                },
            ),
        )

        # TEST one unpaid
        self.assertEqual(resp_one_paid.status_code, status.HTTP_200_OK)
        self.assertEqual(resp_one_paid.json().get("is_paid"), False)
        self.assertEqual(len(resp_one_paid.json().get("tuts_paid")), 1)
        self.assertEqual(len(resp_one_paid.json().get("tuts_unpaid")), 2)

        # Now both of the two Tutorings are paid
        self.tutoring_nico2.paid = True
        self.tutoring_nico2.save()

        resp_all_paid = self.client.get(
            reverse(
                "api:tuts_per_month",
                kwargs={
                    "student_username": "kat.ev",
                    "year": 2022,
                    "month": 1,
                },
            ),
        )
        
        # TEST all paid
        self.assertEqual(resp_all_paid.status_code, status.HTTP_200_OK)
        self.assertEqual(resp_all_paid.json().get("is_paid"), False)
        self.assertEqual(len(resp_all_paid.json().get("tuts_paid")), 2)
        self.assertEqual(len(resp_all_paid.json().get("tuts_unpaid")), 1)
