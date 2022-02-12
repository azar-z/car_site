from django.db import models


class User(models.Model):
    username = models.CharField(max_length=20)
    password = models.CharField(max_length=20)
    credit = models.IntegerField()


class Owner(User):
    pass


class Renter(User):
    pass


class Car(models.Model):
    type = models.CharField(max_length=50)
    plate = models.CharField(max_length=8)
    renter = models.ForeignKey(Renter, null=True, default=None, on_delete=models.SET_NULL)
    owner = models.ForeignKey(Owner, null=False, on_delete=models.CASCADE)





