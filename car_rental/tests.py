from django.test import TestCase
from django.urls import reverse

from car_rental.models import User


def create_user(username, password):
    user = User.objects.create_user(username=username, password=password)
    user.save()
    return user


class LoginViewTest(TestCase):
    def test_login_existing_activated_user(self):
        username = 'Farhad'
        password = '1111'
        create_user(username, password)
        response = self.client.post(reverse('car_rental:login'),
                                    {'username': username, 'password': password})
        self.assertRedirects(response, reverse('car_rental:cars'))

    def test_login_existing_not_activated_user(self):
        username = 'Farhad'
        password = '1111'
        data = {'username': username, 'password': password}
        user = create_user(username, password)
        user.is_active = False
        user.save()
        response = self.client.post(reverse('car_rental:login'), data)
        self.assertFormError(response, 'form', None, "Username and Password didn't match.")

    def test_login_not_existing_user(self):
        username = 'Farhad'
        password = '1111'
        data = {'username': username, 'password': password}
        response = self.client.post(reverse('car_rental:login'), data)
        self.assertFormError(response, 'form', None, "Username and Password didn't match.")
