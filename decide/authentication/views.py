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

from .serializers import UserSerializer

from django.core.mail import BadHeaderError
from .email import send_mail_with_token
from .models import EmailToken
import pyotp
import time


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

class EmailGenerateTokenView(APIView):

    def post(self, request):
        email = request.data.get('email', '')
        if not email:
            return Response({}, status=HTTP_400_BAD_REQUEST)

        user = get_object_or_404(User, email=email)
        if not user:
            return Response({}, status=HTTP_400_BAD_REQUEST)

        try:
            secret = pyotp.random_base32()

            email_token, created = EmailToken.objects.get_or_create(user=user)

            email_token.secret = secret
            email_token.save()

            print(secret)
            totp = pyotp.TOTP(secret, interval=5)
            token = totp.now()
            
            send_mail_with_token(email, token)
        except BadHeaderError:
            return Response({}, status=HTTP_400_BAD_REQUEST)

        return Response({}, status=HTTP_201_CREATED)

class EmailConfirmTokenView(APIView):

    def get(self, request):
        token = request.data.get('token', '')
        if not token:
            return Response({}, status=HTTP_400_BAD_REQUEST)




        return Response({}, status=HTTP_201_CREATED)