from django.shortcuts import render, redirect
from .forms import RegisterForm
from django.contrib.auth import authenticate, login
from django.core.mail import EmailMessage, get_connection
from django.conf import settings


# Create your views here.

