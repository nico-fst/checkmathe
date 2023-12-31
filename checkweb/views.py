from django.contrib.auth import authenticate, login, logout
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, HttpResponseForbidden, HttpResponseNotFound
from django.shortcuts import render, redirect
from django.urls import reverse
from django import forms
from django.views.decorators.csrf import csrf_exempt
from django.core.validators import MinValueValidator
from functools import wraps
from django.db import models
from django.db.models.functions import TruncMonth
from django.contrib.auth.models import Group
from django.db.models import Count
import json

from .models import User, Subject, Tutoring


def teacher_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:  # check if logged in
            return JsonResponse({"error": "Authentication required."}, status=401)
        if request.user.groups.first().name != "Teacher":  # check if teacher
            return JsonResponse({"error": "Permission denied. This action requires the Group 'Teacher'."}, status=403)

        # then call original func
        return view_func(request, *args, **kwargs)

    return _wrapped_view


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
            return render(request, "checkweb/index.html", {"message": "Login successfull"})
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


# New Students
def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        first_name = request.POST["first_name"]
        last_name = request.POST["last_name"]
        email = request.POST["email"]
        phone_number = request.POST["phone_number"]
        ptc = request.POST["personal_teacher_code"]
        group = Group.objects.get(name="Student")  # default: only overwritten if valid PTC

        # Only register as teacher, if a valid PTC was provided
        if ptc == "Amaru":  # TODO as private environment var
            group = Group.objects.get(name="Teacher")
        elif ptc:
            return render(request, "checkweb/register.html", {"message": "Wrong PTC given..."})

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "checkweb/register.html", {"message": "Passwords must match."})

        # Attempt to create new user
        try:
            if phone_number is None:
                user = User.objects.create_user(username, email, password, first_name=first_name, last_name=last_name)
            else:
                user = User.objects.create_user(
                    username,
                    email,
                    password,
                    first_name=first_name,
                    last_name=last_name,
                    phone_number=phone_number,
                )
            user.groups.set([group])
            user.save()
        except IntegrityError:
            return render(
                request,
                "checkweb/register.html",
                {"message": "Username or Email already taken."},
            )
        login(request, user)
        return render(request, "checkweb/index.html", {"message": "Registered successfull"})
    else:
        return render(request, "checkweb/register.html")


class TutForm(forms.Form):
    date = forms.DateField(label="Select a Date", widget=forms.DateInput(attrs={"type": "date"}))
    duration = forms.IntegerField(
        label="Duration",
        validators=[MinValueValidator(0)],
        widget=forms.NumberInput(attrs={"min": 0}),
    )
    subject = forms.ModelChoiceField(queryset=Subject.objects.all(), label="Subject")
    teacher = forms.ModelChoiceField(queryset=User.objects.filter(groups__name="Teacher"), label="Teacher")
    student = forms.ModelChoiceField(queryset=User.objects.filter(groups__name="Student"), label="Student")
    content = forms.CharField(label="Content", widget=forms.Textarea(attrs={"rows": 4, "cols": 50}))


@csrf_exempt
@login_required
def tutoring(request, tut_id=None):
    # POST: create new Tutoring instance
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
        else:
            print("Form errors:", form.errors)

    # if GET or PUT: search Tutoring instance
    try:
        tut = Tutoring.objects.get(id=tut_id)
    except Tutoring.DoesNotExist:
        return JsonResponse({"error": "Tutoring not found."}, status=404)

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


@csrf_exempt
@login_required
def tutoring_view(request, tut_id):
    try:
        tut = Tutoring.objects.get(id=tut_id)
    except Tutoring.DoesNotExist:
        return JsonResponse({"error": f"Tutoring with ID {tut_id} does not exist."}, status=404)

    return render(request, "checkweb/tutoring.html", {"tut": tut})


@csrf_exempt
@login_required
def tutorings(request, user_id):
    tuts_given = Tutoring.objects.filter(teacher=user_id)
    serialized_tuts_given = [t.serialize() for t in tuts_given]

    tuts_taken = Tutoring.objects.filter(student=user_id)
    serialized_tuts_taken = [t.serialize() for t in tuts_taken]

    return JsonResponse(
        {"tuts_given": serialized_tuts_given, "tuts_taken": serialized_tuts_taken},
        safe=False,
    )


def calc_stundenkosten(user, tut):
    return round(user.preis_pro_45 * (tut.duration / 45), 2)


@csrf_exempt
@login_required
def group_tutorings_by_month(request, student_id):
    # group by month, count tuts per month
    result = Tutoring.objects.annotate(month=TruncMonth("date")).values("month").annotate(count=Count("id"))

    month_objects = {}
    for entry in result:
        month = entry["month"]
        # collect relevant Tutorings in current month

        if request.user.groups.first().name == "Teacher":  # filter tutorings given as teacher
            if student_id is not None:  # filter for current month, year, teacher INCLUDING student
                filter_student = User.objects.get(id=student_id)
                tutorings_for_month = Tutoring.objects.filter(
                    date__month=month.month, date__year=month.year, teacher=request.user, student=filter_student
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
    return render(
        request,
        "checkweb/history.html",
        {"tuts_by_month": group_tutorings_by_month(request, student_id)},
    )


@csrf_exempt
@login_required
def new_tut(request):
    return render(request, "checkweb/new_tut.html", {"form": TutForm()})


@csrf_exempt
@login_required
@teacher_required
def delete_tut(request, tut_id):
    try:
        tut = Tutoring.objects.get(id=tut_id)

        # if sb else than the own teacher tries to delete the tut
        if request.user != tut.teacher:
            return HttpResponseForbidden("Permission denied")

        tut.delete()
        return render(request, "checkweb/index.html", {"message": "Success deleting the Tutoring."})
    except Tutoring.DoesNotExist:
        return HttpResponseNotFound(f"Tutoring with ID {tut_id} does not exist.")
