from django.test import TestCase
from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from django.urls import reverse

# Create your tests here.
class LoginTestCase(APITestCase):
    """
    A TestCase for user Login.
    """
    def __init__(self, *args, **kwargs):
        super(LoginTestCase, self).__init__(*args, **kwargs)
        self.user = None

    def set_up(self):
        """
        Set up Test environment with test user and test password.
        """
        self.user = User.objects.create_user(username="testuser", password="testpassword", is_active=True)

    def test_successful_login(self):
        """
        Test the login of a user using test username and password.
        A POST request is sent and if succesful a response is asserted with a status code of '200' and tokens 
        """
        data = {
            'username': 'testuser',
            'password': 'testpassword'
        }
        response = self.client.post(reverse('login'), data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        
class RegistrationTestCase(APITestCase):
    """
    A TestCase for user Account creation.
    """

    def test_successful_registration(self):
        """
        Test successful registration.
        A POST request containing the data variables is sent and 
        a 201 status asserted if the user exists.
        """
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'StrongPassword123',
            'confirm_password': 'StrongPassword123'
        }

        response = self.client.post(reverse('register'), data, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertTrue(User.objects.filter(username='newuser').exists())