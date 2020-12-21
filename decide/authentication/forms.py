from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.db import models
from .models import *


class UserForm(UserCreationForm):
    pass

class ExtraForm(forms.ModelForm):
    class Meta:
        model = Extra
        fields = ['phone', 'double_authentication']



