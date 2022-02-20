import datetime
from math import ceil

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse
from django.utils import timezone


def get_tomorrow():
    return timezone.now() + datetime.timedelta(days=1)


class User(AbstractUser):
    isCarExhibition = models.BooleanField(default=False)
    credit = models.IntegerField(default=0)

    def get_all_requests_of_exhibition(self):
        all_requests = []
        for car in self.cars_owned.all():
            all_requests.extend(car.rentrequest_set.filter(has_result=False))
        return all_requests

    def change_credit(self, delta_credit):
        self.credit += delta_credit
        self.save()

    def __str__(self):
        return self.username + " :  " + ('Car Exhibition' if self.isCarExhibition else 'Renter')


class Car(models.Model):
    car_type = models.CharField(max_length=50, default='type0')
    plate = models.CharField(max_length=8, default='12345678')
    renter = models.ForeignKey(User, null=True, default=None, on_delete=models.SET_NULL, related_name='cars_rented')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name='cars_owned')
    price_per_hour = models.IntegerField(default=10)
    rent_start_time = models.DateTimeField('Start Time', default=timezone.now)
    rent_end_time = models.DateTimeField('End Time', default=timezone.now)

    def __str__(self):
        return str(self.pk) + ". " + self.car_type

    def is_rented(self):
        return self.rent_end_time > timezone.now()

    def set_renter(self, renter):
        self.renter = renter
        self.save()

    def set_owner(self, owner):
        self.owner = owner
        self.save()

    def get_absolute_url(self):
        return reverse('car_rental:car', kwargs={'pk': self.id})


class RentRequest(models.Model):
    is_accepted = models.BooleanField(default=False)
    has_result = models.BooleanField(default=False)
    car = models.ForeignKey(Car, on_delete=models.CASCADE)
    requester = models.ForeignKey(User, on_delete=models.CASCADE)
    rent_start_time = models.DateTimeField('Start Time', default=timezone.now)
    rent_end_time = models.DateTimeField('End Time', default=get_tomorrow)
    creation_time = models.DateTimeField('Request time:', default=timezone.now)

    def accept(self):
        self.is_accepted = True
        self.has_result = True
        self.save()
        car = self.car
        car.renter = self.requester
        car.rent_end_time = self.rent_end_time
        car.rent_start_time = self.rent_start_time
        car.save()
        price = self.get_price()
        self.requester.change_credit(-price)
        car.owner.change_credit(price)

    def reject(self):
        self.is_accepted = False
        self.has_result = True
        self.save()

    def get_price(self):
        delta_time = self.rent_end_time - self.rent_start_time
        delta_hours = delta_time.days * 24 + ceil(delta_time.seconds/3600)
        return delta_hours * self.car.price_per_hour
