from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    isCarExhibition = models.BooleanField(default=False)
    credit = models.IntegerField(default=0)

    def __str__(self):
        return self.username + " :  " + ('Car Exhibition' if self.isCarExhibition else 'Renter')


class Car(models.Model):
    car_type = models.CharField(max_length=50, null=True)
    plate = models.CharField(max_length=8, null=True)
    renter = models.ForeignKey(User, null=True, default=None, on_delete=models.SET_NULL, related_name='cars_rented')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name='cars_owned')

    def __str__(self):
        return self.car_type
