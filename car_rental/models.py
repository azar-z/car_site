import datetime
from math import ceil

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse
from django.utils import timezone


def get_tomorrow():
    return timezone.now() + datetime.timedelta(days=1)


class User(AbstractUser):
    credit = models.IntegerField(default=0)

    def change_credit(self, delta_credit):
        if self.is_staff:
            self.staff.exhibition.change_credit(delta_credit)
        else:
            self.credit += delta_credit
            self.save()

    def __str__(self):
        return self.username + " :  " + ('Car Exhibition' if self.is_staff else 'Renter')


class Exhibition(models.Model):
    name = models.CharField(max_length=200)
    credit = models.IntegerField(default=0)

    def get_all_requests(self):
        return RentRequest.objects.filter(car__owner=self)

    def change_credit(self, delta_credit):
        self.credit += delta_credit
        self.save()


class StaffManager(models.Manager):

    def create(self, *args, **kwargs):
        staff = super(StaffManager, self).create(*args, **kwargs)
        staff.user.is_staff = True
        staff.user.save()
        return staff


class Staff(models.Model):
    is_senior = models.BooleanField(default=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    exhibition = models.ForeignKey(Exhibition, on_delete=models.CASCADE)
    objects = StaffManager()


class Car(models.Model):
    car_type = models.CharField(max_length=50, default='type0')
    plate = models.CharField(max_length=8, default='12345678')
    renter = models.ForeignKey(User, null=True, default=None, on_delete=models.SET_NULL, related_name='cars_rented')
    owner = models.ForeignKey(Exhibition, on_delete=models.CASCADE, null=True, related_name='cars_owned')
    price_per_hour = models.IntegerField(default=10)
    rent_start_time = models.DateTimeField('Start Time', default=timezone.now)
    rent_end_time = models.DateTimeField('End Time', default=timezone.now)
    needs_repair = models.BooleanField(default=False)

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
    price = models.IntegerField(default=0)
    is_accepted = models.BooleanField(default=False)
    has_result = models.BooleanField(default=False)
    car = models.ForeignKey(Car, on_delete=models.CASCADE)
    requester = models.ForeignKey(User, on_delete=models.CASCADE)
    rent_start_time = models.DateTimeField('Start Time', default=timezone.now)
    rent_end_time = models.DateTimeField('End Time', default=get_tomorrow)
    creation_time = models.DateTimeField('Request time:', default=timezone.now)
    responser = models.ForeignKey(Staff, on_delete=models.SET_NULL, default=None, null=True)

    def accept(self, user):
        self.is_accepted = True
        self.has_result = True
        self.responser = user.staff
        self.price = self.get_price()
        self.save()
        car = self.car
        car.renter = self.requester
        car.rent_end_time = self.rent_end_time
        car.rent_start_time = self.rent_start_time
        car.save()
        self.requester.change_credit(-self.price)
        car.owner.change_credit(self.price)

    def reject(self, user):
        self.is_accepted = False
        self.has_result = True
        self.responser = user.staff
        self.price = self.get_price()
        self.save()

    def get_price(self):
        delta_time = self.rent_end_time - self.rent_start_time
        delta_hours = delta_time.days * 24 + ceil(delta_time.seconds/3600)
        return delta_hours * self.car.price_per_hour
