from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import Group
from rest_framework import status
from django.utils import timezone
from rest_framework.test import APIClient
from checkweb.models import Subject, Tutoring, User
from ..serializers import SubjectSerializer
from checkweb.views import calc_stundenkosten
from django.core.files.base import ContentFile
import os
import json


class CreateTutoringIncompleteViewTests(TestCase):
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

        self.kat = User.objects.create_user(
            "kat.ev",
            "kat.ev@web.de",
            "password",
            first_name="Katniss",
            last_name="Everdeen",
        )

        self.client = APIClient()
        self.client.force_authenticate(user=self.nico)

    def test_creation_legal(self):
        resp = self.client.post(
            reverse("api:create_tutoring"),
            {
                "subject_title": "Math",
                "teacher_username": "nico.st",
                "student_username": "kat.ev",
                "yyyy_mm_dd": "2022-01-01",
                "duration_in_min": 60,
                "content": "Sinussatz",
            },
            format="json",
        )

        # TEST created
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Tutoring.objects.all().count(), 1)

    def test_creation_subject(self):
        resp_subject_missing = self.client.post(
            reverse("api:create_tutoring"),
            {
                "teacher_username": "nico.st",
                "student_username": "kat.ev",
                "yyyy_mm_dd": "2022-01-01",
                "duration_in_min": 60,
                "content": "Sinussatz",
            },
            format="json",
        )

        # TEST missing: not created
        self.assertEqual(resp_subject_missing.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Tutoring.objects.all().count(), 0)

        resp_subject_new = self.client.post(
            reverse("api:create_tutoring"),
            {
                "subject_title": "Chemistry",
                "teacher_username": "nico.st",
                "student_username": "kat.ev",
                "yyyy_mm_dd": "2022-01-01",
                "duration_in_min": 60,
                "content": "Sinussatz",
            },
            format="json",
        )

        # TEST new: created
        self.assertEqual(resp_subject_new.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Tutoring.objects.all().count(), 1)

    def test_creation_teacher(self):
        resp_teacher_missing = self.client.post(
            reverse("api:create_tutoring"),
            {
                "subject_title": "Chemistry",
                "student_username": "kat.ev",
                "yyyy_mm_dd": "2022-01-01",
                "duration_in_min": 60,
                "content": "Sinussatz",
            },
            format="json",
        )

        # TEST miissing: not created
        self.assertEqual(resp_teacher_missing.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Tutoring.objects.all().count(), 0)

        resp_teacher_not_existing = self.client.post(
            reverse("api:create_tutoring"),
            {
                "subject_title": "Chemistry",
                "teacher_username": "INVALID_USER",
                "student_username": "kat.ev",
                "yyyy_mm_dd": "2022-01-01",
                "duration_in_min": 60,
                "content": "Sinussatz",
            },
            format="json",
        )

        # TEST not existing: not created
        self.assertEqual(resp_teacher_not_existing.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Tutoring.objects.all().count(), 0)

        resp_teacher_valid = self.client.post(
            reverse("api:create_tutoring"),
            {
                "subject_title": "Chemistry",
                "teacher_username": "nico.st",
                "student_username": "kat.ev",
                "yyyy_mm_dd": "2022-01-01",
                "duration_in_min": 60,
                "content": "Sinussatz",
            },
            format="json",
        )

        # TEST valid: created
        self.assertEqual(resp_teacher_valid.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Tutoring.objects.all().count(), 1)

    def test_creation_student(self):
        resp_student_missing = self.client.post(
            reverse("api:create_tutoring"),
            {
                "subject_title": "Chemistry",
                "teacher_username": "nico.st",
                "yyyy_mm_dd": "2022-01-01",
                "duration_in_min": 60,
                "content": "Sinussatz",
            },
            format="json",
        )

        # TEST miissing: not created
        self.assertEqual(resp_student_missing.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Tutoring.objects.all().count(), 0)

        resp_student_not_existing = self.client.post(
            reverse("api:create_tutoring"),
            {
                "subject_title": "Chemistry",
                "teacher_username": "nico.st",
                "student_username": "INVALID_USER",
                "yyyy_mm_dd": "2022-01-01",
                "duration_in_min": 60,
                "content": "Sinussatz",
            },
            format="json",
        )

        # TEST not existing: not created
        self.assertEqual(resp_student_not_existing.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Tutoring.objects.all().count(), 0)

        resp_student_valid = self.client.post(
            reverse("api:create_tutoring"),
            {
                "subject_title": "Chemistry",
                "teacher_username": "nico.st",
                "student_username": "kat.ev",
                "yyyy_mm_dd": "2022-01-01",
                "duration_in_min": 60,
                "content": "Sinussatz",
            },
            format="json",
        )

        # TEST valid: created
        self.assertEqual(resp_student_valid.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Tutoring.objects.all().count(), 1)

    def test_creation_yyyy_mm_dd(self):
        resp_yyyy_mm_dd_missing = self.client.post(
            reverse("api:create_tutoring"),
            {
                "subject_title": "Chemistry",
                "teacher_username": "nico.st",
                "student_username": "kat.ev",
                "duration_in_min": 60,
                "content": "Sinussatz",
            },
            format="json",
        )

        # TEST missing: not created
        self.assertEqual(resp_yyyy_mm_dd_missing.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Tutoring.objects.all().count(), 0)

        resp_yyyy_mm_dd_invalid = self.client.post(
            reverse("api:create_tutoring"),
            {
                "subject_title": "Chemistry",
                "teacher_username": "nico.st",
                "student_username": "kat.ev",
                "yyyy_mm_dd": "INVALID",
                "duration_in_min": 60,
                "content": "Sinussatz",
            },
            format="json",
        )

        # TEST invalid: not created
        self.assertEqual(resp_yyyy_mm_dd_missing.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Tutoring.objects.all().count(), 0)

        resp_yyyy_mm_dd_in_future = self.client.post(
            reverse("api:create_tutoring"),
            {
                "subject_title": "Chemistry",
                "teacher_username": "nico.st",
                "student_username": "kat.ev",
                "yyyy_mm_dd": "2090-01-01",
                "duration_in_min": 60,
                "content": "Sinussatz",
            },
            format="json",
        )

        # TEST valid: created
        self.assertEqual(resp_yyyy_mm_dd_in_future.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Tutoring.objects.all().count(), 0)
