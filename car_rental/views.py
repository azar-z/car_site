from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.views import generic

from .models import Car
from . import forms


@login_required
def show_cars(request):
    return HttpResponse('car list')


class LoginView(generic.FormView):
    template_name = 'car_rental/login.html'
    form_class = forms.LoginForm

    def form_valid(self, form):
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        user = authenticate(username=username, password=password)
        login(self.request, user)
        return HttpResponseRedirect(reverse('car_rental:cars'))


class CarsView(generic.ListView):
    template_name = 'car_rental/cars.html'
    model = Car
    context_object_name = 'cars'

    def get_queryset(self):
        return Car.objects.filter(renter=None)
