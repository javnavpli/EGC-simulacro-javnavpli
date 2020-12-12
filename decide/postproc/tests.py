from django.test import TestCase

from rest_framework.test import APIClient
from rest_framework.test import APITestCase

from base import mods


class PostProcTestCase(APITestCase):

    def setUp(self):
        self.client = APIClient()
        mods.mock_query(self.client)

    def tearDown(self):
        self.client = None

    def test_identity(self):
        data = {
            'type': 'IDENTITY',
            'options': [
                {'option': 'Option 1', 'number': 1, 'votes': 5},
                {'option': 'Option 2', 'number': 2, 'votes': 0},
                {'option': 'Option 3', 'number': 3, 'votes': 3},
                {'option': 'Option 4', 'number': 4, 'votes': 2},
                {'option': 'Option 5', 'number': 5, 'votes': 5},
                {'option': 'Option 6', 'number': 6, 'votes': 1},
            ]
        }

        expected_result = [
            {'option': 'Option 1', 'number': 1, 'votes': 5, 'postproc': 5},
            {'option': 'Option 5', 'number': 5, 'votes': 5, 'postproc': 5},
            {'option': 'Option 3', 'number': 3, 'votes': 3, 'postproc': 3},
            {'option': 'Option 4', 'number': 4, 'votes': 2, 'postproc': 2},
            {'option': 'Option 6', 'number': 6, 'votes': 1, 'postproc': 1},
            {'option': 'Option 2', 'number': 2, 'votes': 0, 'postproc': 0},
        ]

        response = self.client.post('/postproc/', data, format='json')
        self.assertEqual(response.status_code, 200)

        values = response.json()
        self.assertEqual(values, expected_result)


        
    def test_dhont1(self):
        data = {
            'type': 'DHONT',
            'seats': 10,
            'options': [
                { 'option': 'Option 1', 'number': 1, 'votes': 10 },
                { 'option': 'Option 2', 'number': 2, 'votes': 0 },
                { 'option': 'Option 3', 'number': 3, 'votes': 7 },
                { 'option': 'Option 4', 'number': 4, 'votes': 2 },
                { 'option': 'Option 5', 'number': 5, 'votes': 5 },
                { 'option': 'Option 6', 'number': 6, 'votes': 1 },
            ]
        }
        expected_result = [
            { 'option': 'Option 1', 'number': 1, 'votes': 10, 'postproc': 5 },
            { 'option': 'Option 3', 'number': 3, 'votes': 7, 'postproc': 3 },
            { 'option': 'Option 5', 'number': 5, 'votes': 5, 'postproc': 2 },
            { 'option': 'Option 4', 'number': 4, 'votes': 2, 'postproc': 0 },
            { 'option': 'Option 6', 'number': 6, 'votes': 1, 'postproc': 0 },
            { 'option': 'Option 2', 'number': 2, 'votes': 0, 'postproc': 0 },
        ]

        response = self.client.post('/postproc/', data, format='json')
        self.assertEqual(response.status_code, 200)

        values = response.json()
        self.assertEqual(values, expected_result)

    def test_dhont_2(self):
        seats = 5
        data = {
            'type': 'DHONT',
            'seats': seats,
            'options': [
                {'option': 'Option 1', 'number': 1, 'votes': 10},
                {'option': 'Option 2', 'number': 2, 'votes': 0},
                {'option': 'Option 3', 'number': 3, 'votes': 6},
                {'option': 'Option 4', 'number': 4, 'votes': 4},
                {'option': 'Option 5', 'number': 5, 'votes': 10},
                {'option': 'Option 6', 'number': 6, 'votes': 2},
                {'option': 'Option 7', 'number': 7, 'votes': 6},

            ]
        }

        expected_result = [
            {'option': 'Option 1', 'number': 1, 'votes': 10, 'postproc': 2},
            {'option': 'Option 5', 'number': 5, 'votes': 10, 'postproc': 1},
            {'option': 'Option 3', 'number': 3, 'votes': 6, 'postproc': 1},
            {'option': 'Option 7', 'number': 7, 'votes': 6, 'postproc': 1},
            {'option': 'Option 4', 'number': 4, 'votes': 4, 'postproc': 0},
            {'option': 'Option 6', 'number': 6, 'votes': 2, 'postproc': 0},
            {'option': 'Option 2', 'number': 2, 'votes': 0, 'postproc': 0},
        ]

        response = self.client.post('/postproc/', data, format='json')
        self.assertEqual(response.status_code, 200)

        values = response.json()
        self.assertEqual(values, expected_result)

    # Test en el que no se define la variable type en el json data
    def test_no_type(self):
        seats = 5
        data = {
            'seats': seats,
            'options': [
                {'option': 'Option 1', 'number': 1, 'votes': 9},
                {'option': 'Option 2', 'number': 2, 'votes': 0},
                {'option': 'Option 3', 'number': 3, 'votes': 6},
                {'option': 'Option 4', 'number': 4, 'votes': 4},
                {'option': 'Option 5', 'number': 5, 'votes': 8},
                {'option': 'Option 6', 'number': 6, 'votes': 2},
                {'option': 'Option 7', 'number': 7, 'votes': 5},

            ]
        }
        expected_result = {}

        response = self.client.post('/postproc/', data, format='json')
        self.assertEqual(response.status_code, 400)

        values = response.json()
        self.assertEqual(values, expected_result)

    # Test en el que no se le pasa la variable options en el json data
    def test_no_options(self):
        seats = 5
        data = {
            'type': 'DHONT',
            'seats': seats
        }
        expected_result = {}

        response = self.client.post('/postproc/', data, format='json')
        self.assertEqual(response.status_code, 400)

        values = response.json()
        self.assertEqual(values, expected_result)
    
     # Test en el que no se le pasa la variable seats en el json data
    def test_no_seats(self):
        data = {
            'type': 'DHONT',
            'options': [
                {'option': 'Option 1', 'number': 1, 'votes': 18},
                {'option': 'Option 2', 'number': 2, 'votes': 3},
                {'option': 'Option 3', 'number': 3, 'votes': 6},

            ]
        }
        expected_result = {}

        response = self.client.post('/postproc/', data, format='json')
        self.assertEqual(response.status_code, 400)

        values = response.json()
        self.assertEqual(values, expected_result)
