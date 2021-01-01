from rest_framework import parsers, renderers
from authentication.models import EmailOTPCode
from rest_framework.response import Response
from rest_framework.status import (
        HTTP_200_OK, HTTP_201_CREATED,
        HTTP_400_BAD_REQUEST,
        HTTP_401_UNAUTHORIZED, HTTP_500_INTERNAL_SERVER_ERROR
)
from  smtplib import SMTPException
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from django.views.generic import TemplateView
from django.urls import reverse

from .serializers import EmailOTPCodeSerializer, UserSerializer

from django.core.mail import BadHeaderError
from .email import send_mail_with_token
import pyotp


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
    parser_classes = (parsers.FormParser, parsers.MultiPartParser, parsers.JSONParser,)
    renderer_classes = (renderers.JSONRenderer,)
    serializer_class = EmailOTPCodeSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={'request': request})

        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        callback = serializer.validated_data['callback']

        user = get_object_or_404(User, email=email)
        email_otp_code, created = EmailOTPCode.objects.get_or_create(user=user)

        secret = pyotp.random_base32()

        email_otp_code.callback = callback
        email_otp_code.secret = secret
        email_otp_code.save()

        try:
            totp = pyotp.TOTP(secret, interval=3600)
            token = totp.now()
            link = request.build_absolute_uri(reverse("email-confirm-token", None, [str(user.pk), str(token)]))
            send_mail_with_token(email, link)
        except SMTPException:
            return Response({}, status=HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({}, status=HTTP_200_OK)


class EmailConfirmTokenView(TemplateView):
    template_name = "authentication/email/confirm-email-token.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        user_id = kwargs.get('userId', '')
        token = kwargs.get('token', '')
        
        context['token'] = ''
        context['callback'] = ''

        if user_id:
            try:
                email_otp_code = EmailOTPCode.objects.get(user__pk=user_id)
                if email_otp_code:
                    totp = pyotp.TOTP(email_otp_code.secret, interval=3600)

                    if totp.verify(token):
                        session_token, created = Token.objects.get_or_create(user=email_otp_code.user)
                        context['token'] = session_token.key
                        context['callback'] = email_otp_code.callback

                email_otp_code.delete()
            except ObjectDoesNotExist:
                pass
            
        return context