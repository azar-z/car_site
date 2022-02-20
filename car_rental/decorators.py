from django.core.exceptions import PermissionDenied
from django.utils import timezone

from car_rental.models import User, Car


def user_is_exhibition(function):
    def wrap(request, *args, **kwargs):
        user = User.objects.get(id=request.user.id)
        if user.isCarExhibition:
            return function(request, *args, **kwargs)
        else:
            raise PermissionDenied
    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap


def user_is_owner_and_car_is_not_rented(function):
    def wrap(request, *args, **kwargs):
        user = User.objects.get(id=request.user.id)
        car = Car.objects.get(id=kwargs['pk'])
        if car.owner == user and not car.is_rented() and \
                not car.rentrequest_set.filter(rent_start_time__gt=timezone.now()):
            return function(request, *args, **kwargs)
        else:
            raise PermissionDenied
    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap


def user_requested_exhibition_car(function):
    def wrap(request, *args, **kwargs):
        current_user = User.objects.get(id=request.user.id)
        user = User.objects.get(id=kwargs['pk'])
        if user.rentrequest_set.filter(car__owner=current_user):
            return function(request, *args, **kwargs)
        else:
            raise PermissionDenied
    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap


def car_renter_or_owner(function):
    def wrap(request, *args, **kwargs):
        current_user = User.objects.get(id=request.user.id)
        car = Car.objects.get(id=kwargs['pk'])
        if current_user == car.renter or current_user == car.owner:
            return function(request, *args, **kwargs)
        else:
            raise PermissionDenied
    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap


def car_needs_repair(function):
    def wrap(request, *args, **kwargs):
        car = Car.objects.get(id=kwargs['pk'])
        if car.needs_repair:
            return function(request, *args, **kwargs)
        else:
            raise PermissionDenied
    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap