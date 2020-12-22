import random
import itertools
from django.utils import timezone
from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework.test import APITestCase

from base import mods
from base.tests import BaseTestCase
from census.models import Census
from mixnet.mixcrypt import ElGamal
from mixnet.mixcrypt import MixCrypt
from mixnet.models import Auth
from voting.models import Voting, Question, QuestionOption, QuestionOrder

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

class VotingTestCase(BaseTestCase):

    def setUp(self):
        super().setUp()

    def tearDown(self):
        super().tearDown()

    def encrypt_msg(self, msg, v, bits=settings.KEYBITS):
        pk = v.pub_key
        p, g, y = (pk.p, pk.g, pk.y)
        k = MixCrypt(bits=bits)
        k.k = ElGamal.construct((p, g, y))
        return k.encrypt(msg)

    def create_voting(self):
        q = Question(desc='test question')
        q.save()
        for i in range(5):
            opt = QuestionOption(question=q, option='option {}'.format(i+1))
            opt.save()
        v = Voting(name='test voting', question=q)
        v.save()

        a, _ = Auth.objects.get_or_create(url=settings.BASEURL,
                                          defaults={'me': True, 'name': 'test auth'})
        a.save()
        v.auths.add(a)

        return v

    def create_order_voting(self):
        q = Question(desc='test ordering question')
        q.save()
        for i in range(5):
            opt = QuestionOrder(question=q, option='ordering option {}'.format(i+1), order_number='{}'.format(i+1))
            opt.save()
        v = Voting(name='test ordering voting', question=q)
        v.save()

        a, _ = Auth.objects.get_or_create(url=settings.BASEURL,
                                          defaults={'me': True, 'name': 'test auth'})
        a.save()
        v.auths.add(a)

        return v

    def create_voters(self, v):
        for i in range(100):
            u, _ = User.objects.get_or_create(username='testvoter{}'.format(i))
            u.is_active = True
            u.save()
            c = Census(voter_id=u.id, voting_id=v.id)
            c.save()

    def get_or_create_user(self, pk):
        user, _ = User.objects.get_or_create(pk=pk)
        user.username = 'user{}'.format(pk)
        user.set_password('qwerty')
        user.save()
        return user

    def test_voting_toString(self):
        v = self.create_voting()
        self.assertEquals(str(v), "test voting")
        self.assertEquals(str(v.question), "test question")
        self.assertEquals(str(v.question.options.all()[0]), "option 1 (2)")

    def test_update_voting_400(self):
        v = self.create_voting()
        data = {} #El campo action es requerido en la request
        self.login()
        response = self.client.put('/voting/{}/'.format(v.pk), data, format= 'json')
        self.assertEquals(response.status_code, 400)

    def store_votes(self, v):
        voters = list(Census.objects.filter(voting_id=v.id))
        voter = voters.pop()

        clear = {}
        for opt in v.question.options.all():
            clear[opt.number] = 0
            for i in range(random.randint(0, 5)):
                a, b = self.encrypt_msg(opt.number, v)
                data = {
                    'voting': v.id,
                    'voter': voter.voter_id,
                    'vote': { 'a': a, 'b': b },
                }
                clear[opt.number] += 1
                user = self.get_or_create_user(voter.voter_id)
                self.login(user=user.username)
                voter = voters.pop()
                mods.post('store', json=data)
        return clear

    def test_complete_voting(self):
        v = self.create_voting()
        self.create_voters(v)

        v.create_pubkey()
        v.start_date = timezone.now()
        v.save()

        clear = self.store_votes(v)

        self.login()  # set token
        v.tally_votes(self.token)

        tally = v.tally
        tally.sort()
        tally = {k: len(list(x)) for k, x in itertools.groupby(tally)}

        for q in v.question.options.all():
            self.assertEqual(tally.get(q.number, 0), clear.get(q.number, 0))

        for q in v.postproc:
            self.assertEqual(tally.get(q["number"], 0), q["votes"])

    def test_create_voting_from_api(self):
        data = {'name': 'Example'}
        response = self.client.post('/voting/', data, format='json')
        self.assertEqual(response.status_code, 401)

        # login with user no admin
        self.login(user='noadmin')
        response = mods.post('voting', params=data, response=True)
        self.assertEqual(response.status_code, 403)

        # login with user admin
        self.login()
        response = mods.post('voting', params=data, response=True)
        self.assertEqual(response.status_code, 400)

        data = {
            'name': 'Example',
            'desc': 'Description example',
            'question': 'I want a ',
            'question_opt': ['cat', 'dog', 'horse'],
            'question_ord': []
        }

        response = self.client.post('/voting/', data, format='json')
        self.assertEqual(response.status_code, 201)

    def test_create_ordering_voting_from_api(self):
        data = {'name': 'Example'}

        self.login()
        response = mods.post('voting', params=data, response=True)
        self.assertEqual(response.status_code, 400)

        data = {
            'name': 'Example',
            'desc': 'Description example',
            'question': 'I want a ',
            'question_opt': [],
            'question_ord': ['cat', 'dog', 'horse']
        }

        response = self.client.post('/voting/', data, format='json')
        self.assertEqual(response.status_code, 201)

    def test_update_voting(self):
        voting = self.create_voting()

        data = {'action': 'start'}
        #response = self.client.post('/voting/{}/'.format(voting.pk), data, format='json')
        #self.assertEqual(response.status_code, 401)

        # login with user no admin
        self.login(user='noadmin')
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 403)

        # login with user admin
        self.login()
        data = {'action': 'bad'}
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 400)

        # STATUS VOTING: not started
        for action in ['stop', 'tally']:
            data = {'action': action}
            response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.json(), 'Voting is not started')

        data = {'action': 'start'}
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), 'Voting started')

        # STATUS VOTING: started
        data = {'action': 'start'}
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), 'Voting already started')

        data = {'action': 'tally'}
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), 'Voting is not stopped')

        data = {'action': 'stop'}
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), 'Voting stopped')

        # STATUS VOTING: stopped
        data = {'action': 'start'}
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), 'Voting already started')

        data = {'action': 'stop'}
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), 'Voting already stopped')

        data = {'action': 'tally'}
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), 'Voting tallied')

        # STATUS VOTING: tallied
        data = {'action': 'start'}
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), 'Voting already started')

        data = {'action': 'stop'}
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), 'Voting already stopped')

        data = {'action': 'tally'}
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), 'Voting already tallied')


class VotingViewsTestCase(BaseTestCase):

    def setUp(self):
        options = webdriver.ChromeOptions()
        options.headless = True
        self.driver = webdriver.Chrome(options=options)

        super().setUp()

    def tearDown(self):
        super().tearDown()
        self.driver.quit()

    def create_voting_view_test(self):
        def setup_method(self, method):
            self.driver = webdriver.Chrome()
            self.vars = {}

        def teardown_method(self, method):
            self.driver.quit()

        def wait_for_window(self, timeout = 2):
            time.sleep(round(timeout / 1000))
            wh_now = self.driver.window_handles
            wh_then = self.vars["window_handles"]
            if len(wh_now) > len(wh_then):
                return set(wh_now).difference(set(wh_then)).pop()

        def test_createvoting(self):

            self.driver.get(f'{self.live_server_url}/admin/')
            self.driver.find_element_by_id('id_username').send_keys("admin")
            self.driver.find_element_by_id('id_password').send_keys("qwerty", Keys.ENTER)

            assert self.driver.find_element(By.CSS_SELECTOR, "#content > h1").text == "Site administration"
            self.driver.find_element(By.LINK_TEXT, "Votings").click()
            self.driver.find_element(By.CSS_SELECTOR, ".addlink").click()
            self.driver.find_element(By.ID, "id_name").send_keys("Voting selenium test")
            self.driver.find_element(By.ID, "id_desc").click()
            self.driver.find_element(By.ID, "id_desc").send_keys("Voting selenium test desc")
            self.driver.find_element(By.ID, "id_question").click()
            self.vars["window_handles"] = self.driver.window_handles
            self.driver.find_element(By.CSS_SELECTOR, "#add_id_question > img").click()
            self.vars["win2433"] = self.wait_for_window(2000)
            self.vars["root"] = self.driver.current_window_handle
            self.driver.switch_to.window(self.vars["win2433"])
            self.driver.find_element(By.ID, "id_desc").click()
            self.driver.find_element(By.ID, "id_desc").send_keys("Question description")
            self.driver.find_element(By.ID, "id_options-0-option").click()
            self.driver.find_element(By.ID, "id_options-0-option").send_keys("Option 1")
            self.driver.find_element(By.ID, "id_options-1-option").click()
            self.driver.find_element(By.ID, "id_options-1-option").send_keys("Option 2")
            self.driver.find_element(By.NAME, "_save").click()
            self.driver.close()
            self.vars["window_handles"] = self.driver.window_handles
            self.driver.switch_to.window(self.vars["root"])
            self.vars["win1901"] = self.wait_for_window(2000)
            self.driver.switch_to.window(self.vars["win1901"])
            self.driver.find_element(By.ID, "id_name").send_keys("auth")
            self.driver.find_element(By.ID, "id_url").click()
            self.driver.find_element(By.ID, "id_url").send_keys("localhost:8000")
            self.driver.find_element(By.NAME, "_save").click()
            self.driver.close()
            self.driver.switch_to.window(self.vars["root"])
            self.driver.find_element(By.NAME, "_save").click()
            self.driver.find_element(By.CSS_SELECTOR, ".row1 a").click()
            assert self.driver.find_element(By.CSS_SELECTOR, "#content > h1").text == "Change voting" 