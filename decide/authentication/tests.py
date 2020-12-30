from smtplib import SMTPException

from django.core.mail.message import EmailMultiAlternatives
from authentication.models import EmailOTPCode
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework.test import APITestCase
from unittest import mock

from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from django.core import mail

from base import mods


class AuthTestCase(APITestCase):

    def setUp(self):
        self.client = APIClient()
        mods.mock_query(self.client)
        u = User(username='voter1')
        u.set_password('123')
        u.email = 'voter1@gmail.com'
        u.save()

        u2 = User(username='admin')
        u2.set_password('admin')
        u2.is_superuser = True
        u2.save()

    def tearDown(self):
        self.client = None

    def test_login(self):
        data = {'username': 'voter1', 'password': '123'}
        response = self.client.post('/authentication/login/', data, format='json')
        self.assertEqual(response.status_code, 200)

        token = response.json()
        self.assertTrue(token.get('token'))

    def test_login_fail(self):
        data = {'username': 'voter1', 'password': '321'}
        response = self.client.post('/authentication/login/', data, format='json')
        self.assertEqual(response.status_code, 400)

    def test_getuser(self):
        data = {'username': 'voter1', 'password': '123'}
        response = self.client.post('/authentication/login/', data, format='json')
        self.assertEqual(response.status_code, 200)
        token = response.json()

        response = self.client.post('/authentication/getuser/', token, format='json')
        self.assertEqual(response.status_code, 200)

        user = response.json()
        self.assertEqual(user['id'], 1)
        self.assertEqual(user['username'], 'voter1')

    def test_getuser_invented_token(self):
        token = {'token': 'invented'}
        response = self.client.post('/authentication/getuser/', token, format='json')
        self.assertEqual(response.status_code, 404)

    def test_getuser_invalid_token(self):
        data = {'username': 'voter1', 'password': '123'}
        response = self.client.post('/authentication/login/', data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Token.objects.filter(user__username='voter1').count(), 1)

        token = response.json()
        self.assertTrue(token.get('token'))

        response = self.client.post('/authentication/logout/', token, format='json')
        self.assertEqual(response.status_code, 200)

        response = self.client.post('/authentication/getuser/', token, format='json')
        self.assertEqual(response.status_code, 404)

    def test_logout(self):
        data = {'username': 'voter1', 'password': '123'}
        response = self.client.post('/authentication/login/', data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Token.objects.filter(user__username='voter1').count(), 1)

        token = response.json()
        self.assertTrue(token.get('token'))

        response = self.client.post('/authentication/logout/', token, format='json')
        self.assertEqual(response.status_code, 200)

        self.assertEqual(Token.objects.filter(user__username='voter1').count(), 0)

    def test_register_bad_permissions(self):
        data = {'username': 'voter1', 'password': '123'}
        response = self.client.post('/authentication/login/', data, format='json')
        self.assertEqual(response.status_code, 200)
        token = response.json()

        token.update({'username': 'user1'})
        response = self.client.post('/authentication/register/', token, format='json')
        self.assertEqual(response.status_code, 401)

    def test_register_bad_request(self):
        data = {'username': 'admin', 'password': 'admin'}
        response = self.client.post('/authentication/login/', data, format='json')
        self.assertEqual(response.status_code, 200)
        token = response.json()

        token.update({'username': 'user1'})
        response = self.client.post('/authentication/register/', token, format='json')
        self.assertEqual(response.status_code, 400)

    def test_register_user_already_exist(self):
        data = {'username': 'admin', 'password': 'admin'}
        response = self.client.post('/authentication/login/', data, format='json')
        self.assertEqual(response.status_code, 200)
        token = response.json()

        token.update(data)
        response = self.client.post('/authentication/register/', token, format='json')
        self.assertEqual(response.status_code, 400)

    def test_register(self):
        data = {'username': 'admin', 'password': 'admin'}
        response = self.client.post('/authentication/login/', data, format='json')
        self.assertEqual(response.status_code, 200)
        token = response.json()

        token.update({'username': 'user1', 'password': 'pwd1'})
        response = self.client.post('/authentication/register/', token, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            sorted(list(response.json().keys())),
            ['token', 'user_pk']
        )

    def test_generate_email_token(self):
        data = {'email': 'voter1@gmail.com', 'callback': 'http://domain.es/callback'}
        response = self.client.post('/authentication/email-generate-token/', data, format='json')
        self.assertEqual(response.status_code, 200)
        token = response.json()

        self.assertEqual(EmailOTPCode.objects.filter(user__username='voter1').count(), 1)
        self.assertEqual(len(mail.outbox), 1)

    def test_generate_email_token_send_email(self):
        data = {'email': 'voter1@gmail.com', 'callback': 'http://domain.es/callback'}
        response = self.client.post('/authentication/email-generate-token/', data, format='json')
        self.assertEqual(response.status_code, 200)
        token = response.json()

        self.assertEqual(EmailOTPCode.objects.filter(user__username='voter1').count(), 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Decide - Correo para autenticación')
        self.assertEqual(len(mail.outbox[0].to), 1)
        self.assertEqual(mail.outbox[0].to[0], 'voter1@gmail.com')

    def test_generate_email_token_twice(self):
        data = {'email': 'voter1@gmail.com', 'callback': 'http://domain.es/callback'}
        response = self.client.post('/authentication/email-generate-token/', data, format='json')
        self.assertEqual(response.status_code, 200)

        response = self.client.post('/authentication/email-generate-token/', data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(EmailOTPCode.objects.filter(user__username='voter1').count(), 1)
        self.assertEqual(len(mail.outbox), 2)

    def test_generate_email_token_empty_email(self):
        data = {'email': '', 'callback': 'http://dominio.prueba/callback'}
        response = self.client.post('/authentication/email-generate-token/', data, format='json')
        self.assertEqual(response.status_code, 400)

        self.assertEqual(EmailOTPCode.objects.filter(user__username='voter1').count(), 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_generate_email_token_empty_callback(self):
        data = {'email': 'voter1@gmail.com', 'callback': ''}
        response = self.client.post('/authentication/email-generate-token/', data, format='json')
        self.assertEqual(response.status_code, 400)

        self.assertEqual(EmailOTPCode.objects.filter(user__username='voter1').count(), 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_generate_email_token_wrong_email(self):
        data = {'email': 'no_email@gmail.com', 'callback': 'http://dominio.prueba/callback'}
        response = self.client.post('/authentication/email-generate-token/', data, format='json')
        self.assertEqual(response.status_code, 404)

        self.assertEqual(EmailOTPCode.objects.filter(user__username='voter1').count(), 0)
        self.assertEqual(len(mail.outbox), 0)
    
    def test_generate_email_token_invalid_email(self):
        data = {'email': 'no_email', 'callback': 'http://dominio.prueba/callback'}
        response = self.client.post('/authentication/email-generate-token/', data, format='json')
        self.assertEqual(response.status_code, 400)

        self.assertEqual(EmailOTPCode.objects.filter(user__username='voter1').count(), 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_generate_email_token_wrong_callback(self):
        data = {'email': 'voter1@gmail.com', 'callback': 'no_es_url'}
        response = self.client.post('/authentication/email-generate-token/', data, format='json')
        self.assertEqual(response.status_code, 400)

        self.assertEqual(EmailOTPCode.objects.filter(user__username='voter1').count(), 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_generate_email_token_mail_server_not_working(self):
        data = {'email': 'voter1@gmail.com', 'callback': 'http://dominio.prueba/callback'}
        
        with mock.patch.object(EmailMultiAlternatives, 'send') as mock_method:
            mock_method.side_effect = SMTPException()

            response = self.client.post('/authentication/email-generate-token/', data, format='json')
            self.assertEqual(response.status_code, 500)

        self.assertEqual(EmailOTPCode.objects.filter(user__username='voter1').count(), 1)
        self.assertEqual(len(mail.outbox), 0)