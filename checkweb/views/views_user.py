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
    
def login_demo(request):
    demo_user = User.objects.get(username="demo_user")
    user = authenticate(request, username=demo_user.username, password="123")
    login(request, user)
    return render(
        request,
        "checkweb/index.html",
        {"message": "You signed in as a demo user. Look around and try things out :)"},
    )


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("checkweb:login_view"))


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
                user = User.objects.create_user(
                    username, email, password, first_name=first_name, last_name=last_name
                )
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
