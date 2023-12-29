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
from django.core.validators import MinValueValidator
import json

from .models import Role, User, Subject, Tutoring


def index(request):
    return render(request, "checkweb/index.html")


def login_view(request):
    if request.method == "POST":
        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(
                request,
                "checkweb/login.html",
                {"message": "Invalid username and/or password."},
            )
    else:
        return render(request, "checkweb/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("login"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]
        # role = Role.objects.get(title="Student")

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "checkweb/register.html", {"message": "Passwords must match."})

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "checkweb/register.html", {"message": "Username already taken."})
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "checkweb/register.html")


class TutForm(forms.Form):
    date = forms.DateField(
        label="Select a Date", widget=forms.DateInput(attrs={"type": "date"})
    )
    duration = forms.IntegerField(
        label="Duration",
        validators=[MinValueValidator(0)],
        widget=forms.NumberInput(attrs={"min": 0}),
    )
    subject = forms.ModelChoiceField(queryset=Subject.objects.all(), label="Subject")
    teacher = forms.ModelChoiceField(
        queryset=User.objects.filter(role__title="Teacher"), label="Teacher"
    )
    student = forms.ModelChoiceField(
        queryset=User.objects.filter(role__title="Student"), label="Student"
    )
    content = forms.CharField(
        label="Content", widget=forms.Textarea(attrs={"rows": 4, "cols": 50})
    )


@csrf_exempt
def tutoring(request, tut_id):
    if request.method == "POST":
        form = TutForm(request.POST)
        if form.is_valid():
            new_tut = Tutoring(
                date=form.cleaned_data["date"],
                duration=form.cleaned_data["duration"],
                subject=form.cleaned_data["subject"],
                teacher=form.cleaned_data["teacher"],
                student=form.cleaned_data["student"],
                content=form.cleaned_data["content"],
            )
            new_tut.save()
            return HttpResponseRedirect(reverse("tutoring_view", args=[new_tut.id]))
        # else:

    try:
        tut = Tutoring.objects.get(id=tut_id)
    except Tutoring.DoesNotExist:
        return JsonResponse({"error": "Tutoring not found."}, status=404)

    if request.method == "GET":
        return JsonResponse(tut.serialize())

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


def tutoring_view(request, tut_id):
    try:
        tut = Tutoring.objects.get(id=tut_id)
    except Tutoring.DoesNotExist:
        return JsonResponse(
            {"error": f"Tutoring with ID {tut_id} does not exist."}, status=404
        )

    return render(request, "checkweb/tutoring.html", {"tut": tut})


def tutorings(request, user_id):
    tuts_given = Tutoring.objects.filter(teacher=user_id)
    serialized_tuts_given = [t.serialize() for t in tuts_given]

    tuts_taken = Tutoring.objects.filter(student=user_id)
    serialized_tuts_taken = [t.serialize() for t in tuts_taken]

    return JsonResponse(
        {"tuts_given": serialized_tuts_given, "tuts_taken": serialized_tuts_taken},
        safe=False,
    )

@login_required
def history_view(request):
    tuts_given = Tutoring.objects.filter(teacher=request.user)
    serialized_tuts_given = [t.serialize() for t in tuts_given]

    tuts_taken = Tutoring.objects.filter(student=request.user)
    serialized_tuts_taken = [t.serialize() for t in tuts_taken]

    return render(
        request,
        "checkweb/history.html",
        {"tuts_given": serialized_tuts_given, "tuts_taken": serialized_tuts_taken},
    )


@login_required
def new_tut(request):
    return render(request, "checkweb/new_tut.html", {"form": TutForm()})
