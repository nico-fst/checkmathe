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


def index(request):
    return render(request, "checkweb/index.html")


def calc_stundenkosten(user, tut):
    if user.preis_pro_45 is not None:
        return round(user.preis_pro_45 * (tut.duration / 45), 2)
    else:
        return -9999


@csrf_exempt
@login_required
def group_tutorings_by_month(request, student_id):
    # group by month, count tuts per month
    result = (
        Tutoring.objects.annotate(month=TruncMonth("date"))
        .values("month")
        .annotate(count=Count("id"))
    )

    month_objects = {}
    for entry in result:
        month = entry["month"]
        # collect relevant Tutorings in current month

        if request.user.groups.first().name == "Teacher":  # filter tutorings given as teacher
            if student_id is not None:  # filter for current month, year, teacher INCLUDING student
                filter_student = User.objects.get(id=student_id)
                tutorings_for_month = Tutoring.objects.filter(
                    date__month=month.month,
                    date__year=month.year,
                    teacher=request.user,
                    student=filter_student,
                )
            else:  # filter WITHOUT specific student
                tutorings_for_month = Tutoring.objects.filter(
                    date__month=month.month, date__year=month.year, teacher=request.user
                )
        else:  # filter tutorings taken as student
            tutorings_for_month = Tutoring.objects.filter(
                date__month=month.month, date__year=month.year, student=request.user
            )

        money_for_month = sum(calc_stundenkosten(tut.student, tut) for tut in tutorings_for_month)

        # save collected data
        month_objects[month] = {
            "count": len(tutorings_for_month),
            "tutorings": tutorings_for_month,
            "sum_money": money_for_month,
        }
    return month_objects.items()


@csrf_exempt
@login_required
def history_view(request, student_id=None):
    grouped_tuts = group_tutorings_by_month(request, student_id)
    sorted_tuts = sorted(grouped_tuts, key=lambda x: (x[0].year, x[0].month), reverse=True)

    return render(
        request,
        "checkweb/history.html",
        {"tuts_by_month": sorted_tuts},
    )
