from django import forms
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.core.paginator import Paginator
from django.core.validators import MinValueValidator, FileExtensionValidator
from django.db import IntegrityError, models
from django.db.models import Count, Q
from django.db.models.functions import TruncMonth
from django.http import (
    HttpResponse,
    HttpResponseRedirect,
    JsonResponse,
    HttpResponseForbidden,
    HttpResponseNotFound,
)
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect

import json
from functools import wraps

from ..models import User, Subject, Tutoring


def teacher_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:  # check if logged in
            return JsonResponse({"error": "Authentication required."}, status=401)
        if request.user.groups.first().name != "Teacher":  # check if teacher
            return JsonResponse(
                {"error": "Permission denied. This action requires the Group 'Teacher'."},
                status=403,
            )

        # then call original func
        return view_func(request, *args, **kwargs)

    return _wrapped_view
