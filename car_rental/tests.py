import datetime

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from car_rental.models import User, Car


def create_user(username='Farhad', password='1111'):
    user = User.objects.create_user(username=username, password=password)
    user.save()
    return user


def login_a_user(client):
    user = create_user()
    client.force_login(user)
    return user


def create_car(car_type='type1'):
    car = Car.objects.create(car_type=car_type)
    car.save()
    return car


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


class CarListViewTest(TestCase):

    def test_not_login(self):
        response = self.client.post(reverse('car_rental:cars'))
        self.assertRedirects(response, "/rental/?next=/rental/cars/")

    def test_no_car_exists(self):
        login_a_user(self.client)
        response = self.client.get(reverse('car_rental:cars'))
        self.assertContains(response, 'Available Cars:')
        self.assertContains(response, "There are no available cars for you!")

    def test_not_show_rented_car(self):
        login_a_user(self.client)
        # The default end_time is tomorrow
        car = create_car()
        response = self.client.get(reverse('car_rental:cars'))
        self.assertContains(response, 'Available Cars:')
        self.assertContains(response, "There are no available cars for you!")
        self.assertNotContains(response, car.car_type)

    def test_show_available_car(self):
        login_a_user(self.client)
        car = create_car()
        car.rent_end_time = timezone.now() + datetime.timedelta(hours=-1)
        car.save()
        response = self.client.get(reverse('car_rental:cars'))
        self.assertContains(response, 'Available Cars:')
        self.assertNotContains(response, "There are no available cars for you!")
        self.assertContains(response, car.car_type)
