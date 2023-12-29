from django.contrib.auth import authenticate, login, logout
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django import forms
from django.views.decorators.csrf import csrf_exempt
import json

from .models import Role, User, Subject, Tutoring


def index(request):
    return HttpResponse("siugt")


def tutoring(request, tut_id):
    try:
        tut = Tutoring.objects.get(id=tut_id)
    except Tutoring.DoesNotExist:
        return JsonResponse({"error": "Tutoring not found."}, status=404)

    if request.method == "GET":
        return JsonResponse(tut.serialize())

    elif request.method == "PUT":
        data = json.loads(request.body)
        try:
            if data.get("date") is not None:
                tut.date = data["date"]
            if data.get("duration") is not None:
                tut.duration = data["duration"]
            if data.get("subject") is not None:
                tut.subject = data["subject"]
            if data.get("teacher") is not None:
                tut.teacher = data["teacher"]
            if data.get("student") is not None:
                tut.student = data["student"]
            if data.get("content") is not None:
                tut.content = data["content"]

            tut.save()
            return HttpResponse(status=204)
        except ValueError as e:
            return HttpResponse(f"Illegal value: {e}", status=400)


def tutorings(request, user_id):
    tuts_given = Tutoring.objects.filter(teacher=user_id)
    serialized_tuts_given = [t.serialize() for t in tuts_given]

    tuts_taken = Tutoring.objects.filter(student=user_id)
    serialized_tuts_taken = [t.serialize() for t in tuts_taken]

    return JsonResponse({
        "tuts_given": serialized_tuts_given,
        "tuts_taken": serialized_tuts_taken
        }, safe=False)
