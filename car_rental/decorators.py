from django.core.exceptions import PermissionDenied

from car_rental.models import User


def user_is_staff(function):
    def wrap(request, *args, **kwargs):
        user = request.user
        if user.is_staff:
            return function(request, *args, **kwargs)
        else:
            raise PermissionDenied

    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap


def user_is_not_staff(function):
    def wrap(request, *args, **kwargs):
        user = request.user
        if not user.is_staff:
            return function(request, *args, **kwargs)
        else:
            raise PermissionDenied

    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap
