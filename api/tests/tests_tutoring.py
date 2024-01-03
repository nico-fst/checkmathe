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


class TutoringTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.subject_data = {"title": "Test Subject"}
        self.teach = Group.objects.get(name="Teacher")
        self.url_tut_1 = reverse("api:tutoring_view", kwargs={"tut_id": 1})

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

        self.tut = Tutoring.objects.create(
            date=timezone.now().date(),
            duration=45,
            subject=Subject.objects.create(title="Math"),
            student=self.kat,
            teacher=self.nico,
            content="Lorem ipsum",
        )

    def test_get_tutoring(self):
        # illegal since wrong token
        self.client.credentials(HTTP_AUTHORIZATION=f"Token wrongtoken")
        resp_wrong_token = self.client.get(self.url_tut_1)

        # legal since nico is teacher
        self.client.force_authenticate(user=self.nico)
        resp_authorized = self.client.get(self.url_tut_1)

        # TEST authorized: fetched
        self.assertEqual(resp_authorized.status_code, 200)  # check if successful
        self.assertEqual(
            resp_authorized.json().get("student"), self.kat.serialize()
        )  # check if right tut

        # TEST wrong token: unauthorized
        self.assertEqual(resp_wrong_token.status_code, 401)

    def test_delete_tutoring(self):
        # illegal since kat is not teacher of tut
        self.client.force_authenticate(user=self.kat)
        resp_as_student = self.client.delete(self.url_tut_1)

        # TEST as student: not deleted
        self.assertEqual(resp_as_student.status_code, 403)  # forbidden
        self.assertEqual(Tutoring.objects.all().count(), 1)  # still 1 Tutoring

        # illegal since xavier is not teacher of this tut
        self.client.force_authenticate(user=self.xavier)
        resp_as_wrong_teacher = self.client.delete(self.url_tut_1)

        # TEST wrong teacher: not deleted
        self.assertEqual(resp_as_wrong_teacher.status_code, 403)  # forbidden
        self.assertEqual(Tutoring.objects.all().count(), 1)  # still 1 Tutoring

        # legal since nico is teacher of tut
        self.client.force_authenticate(user=self.nico)
        resp_as_teacher = self.client.delete(self.url_tut_1)

        # TEST legal: deleted
        self.assertEqual(resp_as_teacher.status_code, 200)
        self.assertEqual(Tutoring.objects.all().count(), 0)  # after deletion no Tutoring left

    def test_put_tutoring(self):
        # illegal since xavier is not teacher of this tut
        self.client.force_authenticate(user=self.xavier)
        resp_as_wrong_teacher = self.client.put(self.url_tut_1)

        # TEST as wrong teacher: not put
        self.assertEqual(resp_as_wrong_teacher.status_code, 403)  # forbidden
        self.assertEqual(self.tut.content, "Lorem ipsum")  # Content not changed

        # legal since nico is teacher of this tut
        self.client.force_authenticate(user=self.nico)
        resp_as_own_teacher = self.client.put(
            self.url_tut_1,
            {"new_values": {"content": "New Content. Ananas."}},
            format="json",
        )

        # TEST as own teacher: put (changed content)
        self.assertEqual(resp_as_own_teacher.status_code, 200)
        self.assertEqual(Tutoring.objects.get(id=1).content, "New Content. Ananas.")
