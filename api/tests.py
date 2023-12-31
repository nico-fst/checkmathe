from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from checkweb.models import Subject
from .serializers import SubjectSerializer


class SubjectTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.subject_data = {"name": "Test Subject", "description": "Test Description"}
        self.url_get_subject = reverse("getSubject")
        self.url_add_subject = reverse("addSubject")

    def test_get_subject(self):
        response = self.client.get(self.url_get_subject)
        self.assertEqual(response.status_code, 200)

    def test_add_subject(self):
        response = self.client.post(self.url_add_subject, self.subject_data, format="json")
        self.assertEqual(response.status_code, 200)

    def test_subject_serialization(self):
        subject = Subject.objects.create(title="Test Subject")
        serializer = SubjectSerializer(subject)
        self.assertEqual(Subject.objects.all().count(), 1)
