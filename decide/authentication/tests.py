from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework.test import APITestCase

from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from base.tests import BaseTestCase
from base import mods

from .forms import UserForm, ExtraForm

class AuthTestCase(APITestCase):

    def setUp(self):
        self.client = APIClient()
        mods.mock_query(self.client)
        u = User(username='voter1')
        u.set_password('123')
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


class FormTestCase(TestCase):

    #Formato válido campos usuario
    def test_user_form_correct(self):
        form_data = {'username': 'test1', 'first_name': 'Test1', 'last_name': 'Test1', 'email':'test1@gmail.com', 'password1': 'hola1234', 'password2': 'hola1234'}
        form = UserForm(data=form_data)
        self.assertTrue(form.is_valid())

    #La contraseña de verificación es incorrecta
    def test_user_form_incorrect_passwords(self):
        form_data = {'username': 'test1', 'first_name': 'Test1', 'last_name': 'Test1', 'email':'test1@gmail.com', 'password1': 'hola1234', 'password2': 'adios1234'}
        form = UserForm(data=form_data)
        self.assertFalse(form.is_valid())

    #El formato de la contraseña es incorrecta  
    def test_user_form_incorrect__format_password(self):
        form_data = {'username': 'test1', 'first_name': 'Test1', 'last_name': 'Test1', 'email':'test1@gmail.com', 'password1': 'hola', 'password2': 'hola'}
        form = UserForm(data=form_data)
        self.assertFalse(form.is_valid())

    #Username vacío 
    def test_user_form_blank_username(self):
        form_data = {'username': '', 'first_name': 'Test1', 'last_name': 'Test1', 'email':'test1@gmail.com', 'password1': 'hola1234', 'password2': 'hola1234'}
        form = UserForm(data=form_data)
        self.assertFalse(form.is_valid())

    #Password vacía
    def test_user_form_blank_password(self):
        form_data = {'username': 'test1', 'first_name': 'Test1', 'last_name': 'Test1', 'email':'test1@gmail.com', 'password1': '', 'password2': ''}
        form = UserForm(data=form_data)
        self.assertFalse(form.is_valid())

    #Formato válido campos extra
    def test_extra_form_correct(self):
        form_data = {'phone':'999999999', 'double_authentication':'True'}
        form = ExtraForm(data=form_data)
        self.assertTrue(form.is_valid())

    #Formato incorrecto teléfono (menos de 9 digitos)
    def test_extra_form_incorrect_less_digits(self):
        form_data = {'phone':'123', 'double_authentication':'True'}
        form = ExtraForm(data=form_data)
        self.assertFalse(form.is_valid())

    #Formato incorrecto teléfono (más de 9 digitos)
    def test_extra_form_incorrect_more_digits(self):
        form_data = {'phone':'1234567895', 'double_authentication':'True'}
        form = ExtraForm(data=form_data)
        self.assertFalse(form.is_valid())

    #Formato incorrecto teléfono (caracteres que no son digitos)
    def test_extra_form_incorrect_char(self):
        form_data = {'phone':'123lopujk', 'double_authentication':'True'}
        form = ExtraForm(data=form_data)
        self.assertFalse(form.is_valid())

    #Campo telefono vacío
    def test_extra_form_incorrect_blank_phone(self):
        form_data = {'phone':'', 'double_authentication':'True'}
        form = ExtraForm(data=form_data)
        self.assertFalse(form.is_valid())