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

