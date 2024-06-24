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


class CreateTutoringViewTests(TestCase):
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

        self.kat = User.objects.create_user(
            "kat.ev",
            "kat.ev@web.de",
            "password",
            first_name="Katniss",
            last_name="Everdeen",
        )

        self.client = APIClient()
        self.client.force_authenticate(user=self.nico)

    def test_creation_permisions(self):
        self.client.force_authenticate(user=None)
        resp_unauthorized = self.client.post(
            reverse("api:tutoring"),
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

        # TEST unauthorized: not created
        self.assertEqual(resp_unauthorized.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Tutoring.objects.all().count(), 0)

        self.client.force_authenticate(user=self.kat)
        resp_as_student = self.client.post(
            reverse("api:tutoring"),
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

        # TEST as student: not created
        self.assertEqual(resp_as_student.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Tutoring.objects.all().count(), 0)

        self.client.force_authenticate(user=self.nico)
        resp_valid = self.client.post(
            reverse("api:tutoring"),
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
        self.assertEqual(resp_valid.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Tutoring.objects.all().count(), 1)

    def test_creation_subject(self):
        resp_subject_missing = self.client.post(
            reverse("api:tutoring"),
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
            reverse("api:tutoring"),
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
            reverse("api:tutoring"),
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
            reverse("api:tutoring"),
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
            reverse("api:tutoring"),
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
            reverse("api:tutoring"),
            {
                "subject_title": "Chemistry",
                "teacher_username": "nico.st",
                "yyyy_mm_dd": "2022-01-01",
                "duration_in_min": 60,
                "content": "Sinussatz",
            },
            format="json",
        )

        # TEST missing: not created
        self.assertEqual(resp_student_missing.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Tutoring.objects.all().count(), 0)

        resp_student_not_existing = self.client.post(
            reverse("api:tutoring"),
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
            reverse("api:tutoring"),
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
            reverse("api:tutoring"),
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
            reverse("api:tutoring"),
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
            reverse("api:tutoring"),
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

        # TEST Tutoring in future: not created
        self.assertEqual(resp_yyyy_mm_dd_in_future.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Tutoring.objects.all().count(), 0)

    def test_creation_duration(self):
        resp_valid = self.client.post(
            reverse("api:tutoring"),
            {
                "subject_title": "Chemistry",
                "teacher_username": "nico.st",
                "student_username": "kat.ev",
                "yyyy_mm_dd": "2023-01-01",
                "duration_in_min": 45,
                "content": "Sinussatz",
            },
            format="json",
        )

        # TEST valid: created
        self.assertEqual(resp_valid.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Tutoring.objects.all().count(), 1)

        resp_missing = self.client.post(
            reverse("api:tutoring"),
            {
                "subject_title": "Chemistry",
                "teacher_username": "nico.st",
                "student_username": "kat.ev",
                "yyyy_mm_dd": "2023-01-01",
                "content": "Sinussatz",
            },
            format="json",
        )

        # TEST missing: not created
        self.assertEqual(resp_missing.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Tutoring.objects.all().count(), 1)

        resp_too_small = self.client.post(
            reverse("api:tutoring"),
            {
                "subject_title": "Chemistry",
                "teacher_username": "nico.st",
                "student_username": "kat.ev",
                "yyyy_mm_dd": "2023-01-01",
                "duration_in_min": 0,
                "content": "Sinussatz",
            },
            format="json",
        )

        # TEST value under 1: not created
        self.assertEqual(resp_too_small.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Tutoring.objects.all().count(), 1)

        resp_too_large = self.client.post(
            reverse("api:tutoring"),
            {
                "subject_title": "Chemistry",
                "teacher_username": "nico.st",
                "student_username": "kat.ev",
                "yyyy_mm_dd": "2023-01-01",
                "duration_in_min": 361,
                "content": "Sinussatz",
            },
            format="json",
        )

        # TEST value over 360: not created
        self.assertEqual(resp_too_large.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Tutoring.objects.all().count(), 1)

    def test_creation_pdf(self):
        # valid without file tested above

        self.legal_pdf_content = b"PDF Content"
        self.pdf = SimpleUploadedFile(
            "aloha.pdf", self.legal_pdf_content, content_type="application/pdf"
        )

        self.non_pdf_content = b"Non-PDF Content"
        self.non_pdf_file = ContentFile(self.non_pdf_content, name="non_pdf.txt")

        resp_with_invalid_pdf = self.client.post(
            reverse("api:tutoring"),
            {
                "subject_title": "Chemistry",
                "teacher_username": "nico.st",
                "student_username": "kat.ev",
                "yyyy_mm_dd": "2023-01-01",
                "duration_in_min": 360,
                "content": "Sinussatz",
                "pdf": self.non_pdf_file,
            },
            format="json",
        )

        # TEST invalid file: not created
        self.assertEqual(resp_with_invalid_pdf.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Tutoring.objects.all().count(), 0)

        resp_with_pdf = self.client.post(
            reverse("api:tutoring"),
            {
                "subject_title": "Chemistry",
                "teacher_username": "nico.st",
                "student_username": "kat.ev",
                "yyyy_mm_dd": "2023-01-01",
                "duration_in_min": 360,
                "content": "Sinussatz",
                "pdf": self.pdf,
            },
            format="multipart",
        )

        # TEST invalid file: not created
        self.assertEqual(resp_with_pdf.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Tutoring.objects.all().count(), 1)

        # Prevent PDFs staying stored in filesystem
        Tutoring.objects.get(id=Tutoring.objects.get(date="2023-01-01").id).delete()
