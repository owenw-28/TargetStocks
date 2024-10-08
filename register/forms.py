from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from allauth.account.forms import SignupForm, LoginForm
from django import forms
from django.forms import TextInput,EmailInput,PasswordInput
from django.contrib.auth.models import User
from django import forms


class RegisterForm(SignupForm):
    email = forms.EmailField(max_length=50, required=True, widget = forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email address*'}))
    first_name = forms.CharField(max_length=50, required=True, widget = forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First name*'}))
    last_name = forms.CharField(max_length=50, required=True, widget = forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Surname*'}))

    class Meta:
        model = User
        fields = ("first_name", "last_name", "username", "email", "password1", "password2")


    def __init__(self, *args, **kwargs):
        super(RegisterForm, self).__init__(*args, **kwargs)
        self.fields['password1'].widget = PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password*'})
        self.fields['password2'].widget = PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm password*'})
        self.fields['username'].widget = TextInput(attrs={'class': 'form-control', 'placeholder': 'Username*'})
        for fieldname in ["first_name", "last_name", "username", "email", "password1", "password2"]:
            self.fields[fieldname].help_text = None
            self.fields[fieldname].label = ''


class CustomLoginForm(LoginForm):

    def __init__(self, *args, **kwargs):
        super(CustomLoginForm, self).__init__(*args, **kwargs)
        self.fields['login'].widget = TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'})
        self.fields['password'].widget = PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'})
        for fieldname in ['login', 'password']:
            self.fields[fieldname].label = ''
