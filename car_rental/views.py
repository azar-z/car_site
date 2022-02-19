from django.contrib import messages
from django.contrib.auth import authenticate, login, update_session_auth_hash, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import generic

from .models import Car, RentRequest, User
from . import forms


class LoginView(generic.FormView):
    template_name = 'car_rental/login.html'
    form_class = forms.LoginForm

    def form_valid(self, form):
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        user = authenticate(username=username, password=password)
        login(self.request, user)
        if user.isCarExhibition:
            return HttpResponseRedirect(reverse('car_rental:requests'))
        return HttpResponseRedirect(reverse('car_rental:cars'))


@method_decorator(login_required, name='dispatch')
class CarListView(generic.ListView):
    template_name = 'car_rental/car_list.html'
    model = Car
    context_object_name = 'cars'

    def get_queryset(self):
        current_user = get_object_or_404(User, id=self.request.user.id)
        if current_user.isCarExhibition:
            return current_user.cars_owned.all()
        else:
            return Car.objects.exclude(rent_end_time__gt=timezone.now())


@method_decorator(login_required, name='dispatch')
class CarDetailView(generic.DetailView):
    model = Car
    context_object_name = 'car'
    template_name = 'car_rental/car_detail.html'

    def get_queryset(self):
        return Car.objects.all()


@login_required()
def rent_request_view(request, pk):
    car = get_object_or_404(Car, id=pk)
    try:
        rent_start_time = request.POST['rent_start_time']
        rent_end_time = request.POST['rent_end_time']
    except KeyError:
        return render(request, 'car_rental/car_detail.html',
                      {'car': car, 'error_message': "Please fill the form completely."})
    else:
        rent_req = RentRequest.objects.create(car=car, requester=request.user, rent_end_time=rent_end_time,
                                              rent_start_time=rent_start_time)
        rent_req.save()
    return HttpResponseRedirect(reverse('car_rental:requests'))


@method_decorator(login_required, name='dispatch')
class RentRequestListView(generic.ListView):
    template_name = 'car_rental/request_list.html'
    model = RentRequest
    context_object_name = 'requests'

    def get_queryset(self):
        current_user = get_object_or_404(User, id=self.request.user.id)
        if current_user.isCarExhibition:
            return current_user.get_all_requests_of_exhibition()
        return current_user.rentrequest_set.all()


@login_required()
def answer_requests_view(request):
    user = get_object_or_404(User, id=request.user.id)
    if user.isCarExhibition and request.method == 'POST':
        unanswered_requests = user.get_all_requests_of_exhibition()
        try:
            for unanswered_request in unanswered_requests:
                answer = request.POST[str(unanswered_request.id)]
                if answer == 'yes':
                    unanswered_request.accept()
                else:
                    unanswered_request.reject()

        except KeyError:
            return render(request, 'car_rental/request_list.html', {'requests': unanswered_requests,
                                                                    'error_message': "Please answer the requests!"})
    return HttpResponseRedirect(reverse('car_rental:requests'))


@login_required()
def profile_view(request):
    return render(request, 'car_rental/profile.html')


@login_required()
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, 'Your password was successfully updated!')
            return redirect('car_rental:profile')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'car_rental/change_password.html', {
        'form': form
    })


@method_decorator(login_required, name='dispatch')
class ChangeCreditView(generic.FormView):
    template_name = 'car_rental/change_credit.html'
    form_class = forms.ChangeCreditForm

    def form_valid(self, form):
        delta_credit = form.cleaned_data['delta_credit']
        current_user = get_object_or_404(User, id=self.request.user.id)
        current_user.credit += delta_credit
        current_user.save()
        return HttpResponseRedirect(reverse('car_rental:profile'))


def home_view(request):
    return render(request, 'car_rental/home.html')


@login_required()
def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse('car_rental:home'))
