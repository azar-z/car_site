from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import generic

from .models import Car
from . import forms


class LoginView(generic.FormView):
    template_name = 'car_rental/login.html'
    form_class = forms.LoginForm

    def form_valid(self, form):
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        user = authenticate(username=username, password=password)
        login(self.request, user)
        return HttpResponseRedirect(reverse('car_rental:cars'))


@method_decorator(login_required, name='dispatch')
class CarListView(generic.ListView):
    template_name = 'car_rental/car_list.html'
    model = Car
    context_object_name = 'cars'

    def get_queryset(self):
        return Car.objects.exclude(rent_end_time__gt=timezone.now())


@method_decorator(login_required, name='dispatch')
class CarDetailView(generic.DetailView):
    model = Car
    context_object_name = 'car'
    template_name = 'car_rental/car_detail.html'

    def get_queryset(self):
        return Car.objects.all()
