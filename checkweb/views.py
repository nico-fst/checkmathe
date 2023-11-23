from django.contrib.auth import authenticate, login, logout
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django import forms
from django.views.decorators.csrf import csrf_exempt
import json


# Create your views here.
def index(request):
    return HttpResponse("siuiuii")
