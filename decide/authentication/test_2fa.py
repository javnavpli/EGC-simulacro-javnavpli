
from django.test import TestCase
from django.contrib.staticfiles.testing import StaticLiveServerTestCase

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions
from django.contrib.auth.models import User
from base.tests import BaseTestCase
import itertools
import time
from voting.models import Voting, Question, QuestionOption, QuestionOrder
from authentication.models import Extra
from django.conf import settings
from mixnet.models import Auth
from django.utils import timezone
import logging

class Login2FA(StaticLiveServerTestCase):

    def create_voting(self):
        self.q = Question(desc='Prueba votación')
        self.q.save()
        for i in range(2):
            opt = QuestionOption(question=self.q, option='Opción {}'.format(i+1))
            opt.save()
        self.v= Voting(name='Prueba votación', question=self.q, link="prueba")
        self.v.save()
        self.a, _ = Auth.objects.get_or_create(url=settings.BASEURL,defaults={'me': True, 'name': 'test auth'})
        self.a.save()
        self.v.auths.add(self.a)
        self.v.create_pubkey()
        self.v.start_date = timezone.now()
        self.v.save()
        
    def createUser2fa(self):
        self.user_with_2fa = User(username='userWith2fa')
        self.user_with_2fa.set_password('qwerty')
        self.user_with_2fa.save()

        self.extra = Extra(phone='020304050')
        self.extra.totp_code = 'S3K3TPI5MYA2M67V'
        self.extra.save()
        totp_code = pyotp.TOTP(self.extra.totp_code).now()

        # data = {'username': self.user_with_2fa.username, 'password': self.user_with_2fa.password, 'totp_code': totp_code}
        # response = mods.post('authentication/login', json=data, response=True)
        # self.assertEqual(response.status_code, 200)


    def setUp(self):

        self.base = BaseTestCase()
        self.base.setUp()

        self.vars = {}
        self.create_voting()
        self.createUser2fa()
        options = webdriver.ChromeOptions()
        options.headless = True
        self.driver = webdriver.Chrome(options=options)

        super().setUp()

    def tearDown(self):
        super().tearDown()
        self.driver.quit()
        self.base.tearDown()
        self.v.delete()

    def test_login_correct_2fa(self):
        self.driver.get(f'{self.live_server_url}/booth/{self.v.pk}')
        assert self.driver.find_element(By.CSS_SELECTOR, ".voting > h1").text == f"{self.v.pk} - Prueba votación"
        self.driver.find_element(By.CSS_SELECTOR, ".custom-control:nth-child(2)").click()
        self.driver.find_element(By.CSS_SELECTOR, ".custom-control:nth-child(2) > .custom-control-label").click()
        self.driver.find_element(By.ID, "username").click()
        self.driver.find_element(By.ID, "username").send_keys("userWith2fa")
        self.driver.find_element(By.ID, "password").send_keys("qwerty")
        self.driver.find_element(By.ID, "totp_code").click()
        totp_code = pyotp.TOTP(self.extra.totp_code).now()
        self.driver.find_element(By.ID, "totp_code").send_keys(totp_code)
        self.driver.find_element(By.CSS_SELECTOR, ".btn").click()
        assert self.driver.find_element(By.CSS_SELECTOR, ".btn").text == "Vote"

    #Usuario introduce una contraseña incorrecta de su cuenta de Github
    # def test_login_incorrect_password(self):
    #     #Redirección a la votación creada
    #     self.driver.get(f'{self.live_server_url}/booth/{self.v.pk}')
    #     assert self.driver.find_element(By.CSS_SELECTOR, ".voting > h1").text == f"{self.v.pk} - Prueba votación"
    #     #Inicio sesión con github
    #     self.driver.find_element(By.LINK_TEXT, "Iniciar sesión con Github").click()
    #     self.driver.find_element(By.CSS_SELECTOR, "p:nth-child(2)").click()
    #     assert self.driver.find_element(By.CSS_SELECTOR, "strong:nth-child(3)").text == "AuthenticationApp"
    #     self.driver.find_element(By.ID, "login_field").click()
    #     self.driver.find_element(By.ID, "login_field").send_keys("decideautenticacion")
    #     self.driver.find_element(By.ID, "password").click()
    #     self.driver.find_element(By.ID, "password").send_keys("1234")
    #     self.driver.find_element(By.NAME, "commit").click()
    #     #Mensaje error
    #     assert self.driver.find_element(By.CSS_SELECTOR, ".flash > .container-lg").text == "Incorrect username or password."

    #Usuario introduce un username incorrecto de su cuenta de Github
    # def test_login_incorrect_username(self):
    #     #Redirección a la votación creada
    #     self.driver.get(f'{self.live_server_url}/booth/{self.v.pk}')
    #     assert self.driver.find_element(By.CSS_SELECTOR, ".voting > h1").text == f"{self.v.pk} - Prueba votación"
    #     #Inicio sesión con github
    #     self.driver.find_element(By.LINK_TEXT, "Iniciar sesión con Github").click()
    #     self.driver.find_element(By.CSS_SELECTOR, "p:nth-child(2)").click()
    #     assert self.driver.find_element(By.CSS_SELECTOR, "strong:nth-child(3)").text == "AuthenticationApp"
    #     self.driver.find_element(By.ID, "login_field").click()
    #     self.driver.find_element(By.ID, "login_field").send_keys("decideautenticacionn")
    #     self.driver.find_element(By.ID, "password").click()
    #     self.driver.find_element(By.ID, "password").send_keys("pruebadecide11")
    #     self.driver.find_element(By.NAME, "commit").click()
    #     #Mensaje error
    #     assert self.driver.find_element(By.CSS_SELECTOR, ".flash > .container-lg").text == "Incorrect username or password."