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


class TutForm(forms.Form):
    date = forms.DateField(label="Select a Date", widget=forms.DateInput(attrs={"type": "date"}))
    duration = forms.IntegerField(
        label="Duration",
        validators=[MinValueValidator(0)],
        widget=forms.NumberInput(attrs={"min": 0}),
    )
    subject = forms.ModelChoiceField(queryset=Subject.objects.all(), label="Subject")
    teacher = forms.ModelChoiceField(
        queryset=User.objects.filter(groups__name="Teacher"), label="Teacher"
    )
    student = forms.ModelChoiceField(
        queryset=User.objects.filter(groups__name="Student"), label="Student"
    )
    content = forms.CharField(label="Content", widget=forms.Textarea(attrs={"rows": 4, "cols": 50}))
    pdf = forms.FileField(
        label="Upload PDF",
        required=False,
        widget=forms.FileInput(attrs={"accept": ".pdf"}),
        validators=[FileExtensionValidator(allowed_extensions=["pdf"])],
    )


@csrf_exempt
@login_required
def new_tut(request):
    return render(request, "checkweb/new_tut.html", {"form": TutForm()})


@csrf_exempt
@login_required
def tutoring(request, tut_id=None):
    """changes Tutoring DB

    POST: Creates new Tutoring instance,
    GET: Returns serializes Tut, else None
    PUT: Updates Tut with given values
    DELETE: deletes Tut if found and permission
    """

    # POST: create new Tutoring instance
    if request.method == "POST":
        form = TutForm(request.POST, request.FILES)
        if form.is_valid():
            new_tut = Tutoring(
                date=form.cleaned_data["date"],
                duration=form.cleaned_data["duration"],
                subject=form.cleaned_data["subject"],
                teacher=form.cleaned_data["teacher"],
                student=form.cleaned_data["student"],
                content=form.cleaned_data["content"],
                pdf=form.cleaned_data["pdf"],
            )
            new_tut.save()
            return HttpResponseRedirect(reverse("checkweb:tutoring_view", args=[new_tut.id]))
        else:
            print("Form errors:", form.errors)

    # GET, PUT: firstly search for Tutoring instance
    try:
        tut = Tutoring.objects.get(id=tut_id)
    except Tutoring.DoesNotExist:
        return JsonResponse({"error": f"Tutoring  with ID {tut_id} not found."}, status=404)

    # GET: return serializes Tutoring
    if request.method == "GET":
        return JsonResponse(tut.serialize())

    # PUT: update given values
    elif request.method == "PUT":
        data = json.loads(request.body)
        try:
            # change every item reveiced
            for key, value in data.items():
                setattr(tut, key, value)
            tut.save()
            return HttpResponse(status=204)
        except ValueError as e:
            return HttpResponse(f"Illegal value: {e}", status=400)

    # DELETE: delete Tut if found and permission
    elif request.method == "DELETE":
        try:
            # Guard: if sb else than the own teacher tries to delete the tut
            if request.user != tut.teacher:
                return HttpResponseForbidden("Permission denied")

            tut.delete()
            return render(
                request, "checkweb/index.html", {"message": "Success deleting the Tutoring."}
            )
        except Tutoring.DoesNotExist:
            return HttpResponseNotFound(f"Tutoring with ID {tut_id} does not exist.")


@csrf_exempt
@login_required
def tutoring_view(request, tut_id):
    try:
        tut = Tutoring.objects.get(id=tut_id)
        if tut.student.id != request.user.id and tut.teacher.id != request.user.id:
            return HttpResponseForbidden("Permission denied")

        return render(request, "checkweb/tutoring.html", {"tut": tut})
    except Tutoring.DoesNotExist:
        return JsonResponse({"error": f"Tutoring with ID {tut_id} not found."}, status=404)
