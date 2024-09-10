from django.test import TestCase
from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from django.urls import reverse

# Create your tests here.
class LoginTestCase(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpassword", is_active=True)

    def test_successful_login(self):
        data = {
            'username': 'testuser',
            'password': 'testpassword'
        }
        response = self.client.post(reverse('login'), data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        
class RegistrationTestCase(APITestCase):

    def test_successful_registration(self):
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'StrongPassword123',
            'confirm_password': 'StrongPassword123'
        }

        response = self.client.post(reverse('register'), data, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertTrue(User.objects.filter(username='newuser').exists())