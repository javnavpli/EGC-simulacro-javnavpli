from rest_framework.response import Response
from rest_framework.status import (
        HTTP_201_CREATED,
        HTTP_400_BAD_REQUEST,
        HTTP_401_UNAUTHORIZED
)
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from django import forms
from .serializers import UserSerializer
from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.contrib.auth.forms import UserCreationForm
from django.template import RequestContext
from django.contrib import messages
from django.contrib.auth import login, authenticate
import pyotp


from .forms import UserForm, ExtraForm
from .models import Extra

def registro_usuario(request):
    if request.POST.get("base32secret"):
        base32secret = request.POST.get("base32secret")
    else:
        base32secret = pyotp.random_base32()
    url_totp = pyotp.totp.TOTP(base32secret).provisioning_uri(issuer_name="Decide App")

    user_form = UserForm()
    extra_form = ExtraForm(initial={'base32secret':base32secret})

    if request.method == 'POST':
        extra_form = ExtraForm(request.POST,"extra_form")
        user_form = UserForm(request.POST,"user_form")
        if extra_form.is_valid() and user_form.is_valid():
            user_form.save()
            username = user_form.cleaned_data["username"]
            phone = extra_form.cleaned_data["phone"]
            base32secret = extra_form.cleaned_data["base32secret"]
            user = User.objects.get(username=username)
            Extra.objects.create(phone=phone, totp_code=base32secret, user=user)   
            login(request, user) 
            return redirect(to='inicio')
            
    formularios = {
        "user_form":user_form,
        "extra_form":extra_form,
        "url_totp":url_totp,
        "base32secret":base32secret,
    }       
    return render(request, 'registro.html', formularios)

def inicio(request):
    return render(request, 'inicio.html')
    


def home(request):
    return render(request, 'index.html')


class GetUserView(APIView):
    def post(self, request):
        key = request.data.get('token', '')
        tk = get_object_or_404(Token, key=key)
        return Response(UserSerializer(tk.user, many=False).data)


class LogoutView(APIView):
    def post(self, request):
        key = request.data.get('token', '')
        try:
            tk = Token.objects.get(key=key)
            tk.delete()
        except ObjectDoesNotExist:
            pass

        return Response({})


class RegisterView(APIView):
    def post(self, request):
        key = request.data.get('token', '')
        tk = get_object_or_404(Token, key=key)
        if not tk.user.is_superuser:
            return Response({}, status=HTTP_401_UNAUTHORIZED)

        username = request.data.get('username', '')
        pwd = request.data.get('password', '')
        if not username or not pwd:
            return Response({}, status=HTTP_400_BAD_REQUEST)

        try:
            user = User(username=username)
            user.set_password(pwd)
            user.save()
            token, _ = Token.objects.get_or_create(user=user)
        except IntegrityError:
            return Response({}, status=HTTP_400_BAD_REQUEST)
        return Response({'user_pk': user.pk, 'token': token.key}, HTTP_201_CREATED)



