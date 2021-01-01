
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
from django.contrib.auth.models import User
from base.tests import BaseTestCase
import itertools
import time
from voting.models import Voting, Question, QuestionOption, QuestionOrder
from django.conf import settings
from mixnet.models import Auth
from django.utils import timezone
from census.models import Census

class Github(StaticLiveServerTestCase):
    
    def create_voting(self,l):
        q = Question(desc='Prueba votación')
        q.save()
        for i in range(2):
            opt = QuestionOption(question=q, option='Opción {}'.format(i+1))
            opt.save()
        v = Voting(name='Prueba votación', question=q, link="prueba"+str(l))
        v.save()

        a, _ = Auth.objects.get_or_create(url=settings.BASEURL,
                                          defaults={'me': True, 'name': 'test auth'})
        a.save()
        v.auths.add(a)
        v.create_pubkey()
        v.start_date = timezone.now()
        v.save()

    def setUp(self):

        self.base = BaseTestCase()
        self.base.setUp()

        self.vars = {}
       
        options = webdriver.ChromeOptions()
        options.headless = True
        self.driver = webdriver.Chrome(options=options)

        super().setUp()

    def tearDown(self):
        super().tearDown()
        self.driver.quit()
        self.base.tearDown()

    #Función de votación de las pruebas
    

    #Usuario se autentica correctamente mediante github y llega a la página de la votación creada
    def test_login_correcto_github(self):
        #Creación de la votación para la prueba
        self.create_voting(1)
        #Redirección a la votación creada
        self.driver.get(f'{self.live_server_url}/booth/1')
        assert self.driver.find_element(By.CSS_SELECTOR, ".voting > h1").text == "1 - Prueba votación"
        #Inicio sesión con github
        self.driver.find_element(By.LINK_TEXT, "Iniciar sesión con Github").click()
        self.driver.find_element(By.CSS_SELECTOR, "p:nth-child(2)").click()
        assert self.driver.find_element(By.CSS_SELECTOR, "strong:nth-child(3)").text == "AuthenticationApp"
        self.driver.find_element(By.ID, "login_field").click()
        self.driver.find_element(By.ID, "login_field").send_keys("decideautenticacion")
        self.driver.find_element(By.ID, "password").click()
        self.driver.find_element(By.ID, "password").send_keys("pruebadecide11")
        self.driver.find_element(By.NAME, "commit").click()
        #Esperamos 4 segundos debido a las diferentes redirecciones hasta llegar de nuevo a la página de votación
        time.sleep(4)
        assert self.driver.find_element(By.CSS_SELECTOR, ".btn").text == "Vote"
    
        

    #Usuario introduce una contraseña errónea en la página login ofrecida por github
    
    def test_login_incorrecto_github(self):
        #Creación de la votación para la prueba
        self.create_voting(2)
        #Redirección a la votación creada
        self.driver.get(f'{self.live_server_url}/booth/2')
        assert self.driver.find_element(By.CSS_SELECTOR, ".voting > h1").text == "2 - Prueba votación"
        #Inicio sesión con github
        self.driver.find_element(By.LINK_TEXT, "Iniciar sesión con Github").click()
        self.driver.find_element(By.CSS_SELECTOR, "p:nth-child(2)").click()
        assert self.driver.find_element(By.CSS_SELECTOR, "strong:nth-child(3)").text == "AuthenticationApp"
        self.driver.find_element(By.ID, "login_field").click()
        self.driver.find_element(By.ID, "login_field").send_keys("decideautenticacion")
        self.driver.find_element(By.ID, "password").click()
        self.driver.find_element(By.ID, "password").send_keys("1234")
        self.driver.find_element(By.NAME, "commit").click()
        #Mensaje error
        assert self.driver.find_element(By.CSS_SELECTOR, ".flash > .container-lg").text == "Incorrect username or password."
    
    #El usuario se desloguea correctamente, siendo redireccionado a la página de inicio, pidiendole las credenciales de nuevo para entrar a la votación deseada
    def test_logout(self):
        #Creación de la votación para la prueba
        self.create_voting(3)
        #Redirección a la votación creada
        self.driver.get(f'{self.live_server_url}/booth/3')
        assert self.driver.find_element(By.CSS_SELECTOR, ".voting > h1").text == "3 - Prueba votación"
        #Inicio sesión con github
        self.driver.find_element(By.LINK_TEXT, "Iniciar sesión con Github").click()
        self.driver.find_element(By.CSS_SELECTOR, "p:nth-child(2)").click()
        assert self.driver.find_element(By.CSS_SELECTOR, "strong:nth-child(3)").text == "AuthenticationApp"
        self.driver.find_element(By.ID, "login_field").click()
        self.driver.find_element(By.ID, "login_field").send_keys("decideautenticacion")
        self.driver.find_element(By.ID, "password").click()
        self.driver.find_element(By.ID, "password").send_keys("pruebadecide11")
        self.driver.find_element(By.NAME, "commit").click()
        #Esperamos 4 segundos debido a las diferentes redirecciones hasta llegar de nuevo a la página de votación
        time.sleep(4)
        self.driver.set_window_size(1386, 752)
        assert self.driver.find_element(By.CSS_SELECTOR, ".voting > h1").text == "3 - Prueba votación"
        #Hacemos click en el botón de logout para Github
        self.driver.find_element(By.LINK_TEXT, "logout GitHub").click()
        #Comprobamos que hemos vuelto a la página login de la aplicación
        self.driver.find_element(By.ID, "__BVID__16__BV_label_").click()
        assert self.driver.find_element(By.ID, "__BVID__16__BV_label_").text == "Username"
        self.driver.find_element(By.ID, "__BVID__18__BV_label_").click()
        assert self.driver.find_element(By.ID, "__BVID__18__BV_label_").text == "Password"
        #Si le damos a iniciar sesión mediante github de nuevo iniciará sesión con la cuenta que este logeada en la página github, a no ser que cerremos sesión en esta
        self.driver.find_element(By.LINK_TEXT, "Iniciar sesión con Github").click()
        assert self.driver.find_element(By.CSS_SELECTOR, ".voting > h1").text == "3 - Prueba votación"
        self.driver.find_element(By.LINK_TEXT, "logout GitHub").click()
        #Si queremos iniciar sesión con una cuenta de github diferente, cerramos sesión en la página de github y al darle de nuevo a iniciar sesión con github, 
        #nos pedirá las credenciales de una nueva cuenta.
        self.driver.get("https://github.com/logout")
        self.driver.set_window_size(1386, 752)
        self.driver.find_element(By.CSS_SELECTOR, ".btn").click()
        #Al dar al enlace de iniciar sesión mediante Github si hemos cerrado sesión, debe aparecer de nuevo la página login ofrecida por este servicio
        self.driver.get(f'{self.live_server_url}/booth/3')
        self.driver.find_element(By.LINK_TEXT, "Iniciar sesión con Github").click()
        self.driver.find_element(By.CSS_SELECTOR, "p:nth-child(2)").click()
        assert self.driver.find_element(By.CSS_SELECTOR, "strong:nth-child(3)").text == "AuthenticationApp"
    
        

    
     
        