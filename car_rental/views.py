from django.contrib import messages
from django.contrib.auth import authenticate, login, update_session_auth_hash, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm, UserCreationForm
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import generic

from . import decorators
from .forms import StaffCreationForm
from .models import Car, RentRequest, User, Exhibition, Staff
from . import forms as my_forms


def get_current_user(request):
    return User.objects.get(id=request.user.id)


class LoginView(generic.FormView):
    template_name = 'car_rental/login.html'
    form_class = my_forms.LoginForm

    def form_valid(self, form):
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        user = authenticate(username=username, password=password)
        login(self.request, user)
        return HttpResponseRedirect(reverse('car_rental:home'))


@method_decorator(login_required, name='dispatch')
class CarListView(generic.ListView):
    template_name = 'car_rental/car_list.html'
    model = Car
    context_object_name = 'cars'

    def get_queryset(self):
        current_user = get_object_or_404(User, id=self.request.user.id)
        if current_user.is_staff:
            return current_user.staff.exhibition.cars_owned.all()
        else:
            return Car.objects.exclude(rent_end_time__gt=timezone.now()).filter(needs_repair=False)


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
        if current_user.is_staff:
            return current_user.staff.exhibition.get_all_requests().order_by('rent_start_time').filter(has_result=False)
        return current_user.rentrequest_set.all().order_by('-rent_start_time')


@login_required()
def answer_requests_view(request):
    user = get_object_or_404(User, id=request.user.id)
    if user.is_staff and request.method == 'POST':
        unanswered_requests = user.staff.exhibition.get_all_requests()
        try:
            for unanswered_request in unanswered_requests:
                answer = request.POST[str(unanswered_request.id)]
                if answer == 'yes':
                    unanswered_request.accept(user)
                else:
                    unanswered_request.reject(user)

        except KeyError:
            return render(request, 'car_rental/request_list.html',
                          {'requests': unanswered_requests, 'error_message': "Please answer the requests!"})
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
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password was successfully updated!')
            return redirect('car_rental:profile')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'car_rental/change_password.html', {'form': form})


@method_decorator(login_required, name='dispatch')
@method_decorator(decorators.staff_is_senior, name='dispatch')
class ChangeCreditView(generic.FormView):
    template_name = 'car_rental/change_credit.html'
    form_class = my_forms.ChangeCreditForm

    def form_valid(self, form):
        delta_credit = form.cleaned_data['delta_credit']
        current_user = get_object_or_404(User, id=self.request.user.id)
        current_user.change_credit(delta_credit)
        return HttpResponseRedirect(reverse('car_rental:profile'))


def home_view(request):
    return render(request, 'car_rental/home.html')


@login_required()
def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse('car_rental:home'))


def create_exhibition(user):
    exhibition = Exhibition.objects.create(name=user.username)
    exhibition.save()
    senior_staff = Staff.objects.create(exhibition=exhibition, is_senior=True, user=user)
    senior_staff.save()


def signup(request):
    if request.method == 'POST':
        form = my_forms.SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user_type = form.cleaned_data.get('user_type')
            user = authenticate(username=username, password=raw_password)
            if user_type == 'EX':
                create_exhibition(user)
            login(request, user)
            return HttpResponseRedirect(reverse('car_rental:home'))
    else:
        form = my_forms.SignUpForm()
    return render(request, 'car_rental/signup.html', {'form': form})


@method_decorator(login_required, name='dispatch')
@method_decorator(decorators.user_is_staff, name='dispatch')
class AddCarView(generic.CreateView):
    model = Car
    template_name = 'car_rental/add_car.html'
    fields = ['car_type', 'plate', 'price_per_hour']

    def form_valid(self, form):
        response = super(AddCarView, self).form_valid(form)
        current_user = User.objects.get(id=self.request.user.id)
        self.object.set_owner(current_user.staff.exhibition)
        return response


@method_decorator(login_required, name='dispatch')
@method_decorator(decorators.user_is_staff, name='dispatch')
class EditCarView(generic.UpdateView):
    model = Car
    template_name = 'car_rental/edit_car.html'
    fields = ['price_per_hour']

    def get_queryset(self):
        current_user = get_current_user(self.request)
        return current_user.staff.exhibition.cars_owned.filter(rent_end_time__lte=timezone.now())


@method_decorator(login_required, name='dispatch')
class DeleteCarView(generic.DeleteView):
    model = Car
    template_name = 'car_rental/delete_car.html'

    def get_success_url(self):
        return reverse('car_rental:cars')

    def get_queryset(self):
        current_user = get_current_user(self.request)
        return current_user.staff.exhibition.cars_owned.filter(rent_end_time__lte=timezone.now())


@method_decorator(login_required, name='dispatch')
class UserDetailView(generic.DetailView):
    model = User
    context_object_name = 'user'
    template_name = 'car_rental/user_info.html'

    def get_queryset(self):
        current_user = get_current_user(self.request)
        queryset = User.objects.none()
        if current_user.is_staff:
            for rent_request in current_user.staff.exhibition.get_all_requests():
                queryset |= User.objects.filter(id=rent_request.requester.id)
        return queryset


@method_decorator(login_required, name='dispatch')
class NeedRepairCarView(generic.UpdateView):
    model = Car
    template_name = 'car_rental/need_repair.html'
    fields = ['needs_repair']

    def form_valid(self, form):
        response = super(NeedRepairCarView, self).form_valid(form)
        car = self.object
        if car.renter == get_current_user(self.request):
            if car.needs_repair:
                car.renter.change_credit(-100)
                car.owner.change_credit(100)
            car.needs_repair = False
            car.save()
        return response

    def get_queryset(self):
        current_user = get_current_user(self.request)
        if current_user.is_staff:
            return current_user.staff.exhibition.cars_owned.all()
        else:
            return current_user.cars_rented.filter(needs_repair=True)


@method_decorator(login_required, name='dispatch')
@method_decorator(decorators.user_is_staff, name='dispatch')
@method_decorator(decorators.staff_is_senior, name='dispatch')
class CreateStaffView(generic.CreateView):
    model = User
    form_class = StaffCreationForm
    template_name = 'car_rental/add_staff.html'

    def get_success_url(self):
        return reverse('car_rental:staff')

    def get_queryset(self):
        return User.objects.all()

    def form_valid(self, form):
        current_user = self.request.user
        response = super(CreateStaffView, self).form_valid(form)
        exhibition = current_user.staff.exhibition
        staff = Staff.objects.create(user=self.object, exhibition=exhibition)
        if form.cleaned_data.get('staff_type') == 'S':
            staff.is_senior = True
        staff.save()
        return response


@method_decorator(login_required, name='dispatch')
@method_decorator(decorators.user_is_staff, name='dispatch')
@method_decorator(decorators.staff_is_senior, name='dispatch')
class StaffListView(generic.ListView):
    model = Staff
    template_name = 'car_rental/staff_list.html'
    context_object_name = 'staff_list'

    def get_queryset(self):
        return self.request.user.staff.exhibition.staff_set.exclude(id=self.request.user.staff.id)


@method_decorator(login_required, name='dispatch')
@method_decorator(decorators.user_is_staff, name='dispatch')
@method_decorator(decorators.staff_is_senior, name='dispatch')
class StaffDetailView(generic.DetailView):
    model = Staff
    template_name = 'car_rental/staff_detail.html'

    def get_queryset(self):
        return self.request.user.staff.exhibition.staff_set.exclude(id=self.request.user.staff.id)


@method_decorator(login_required, name='dispatch')
@method_decorator(decorators.user_is_staff, name='dispatch')
@method_decorator(decorators.staff_is_senior, name='dispatch')
class StaffDeleteView(generic.DeleteView):
    model = User
    template_name = 'car_rental/delete_staff.html'

    def get_success_url(self):
        return reverse('car_rental:staff')

    def get_queryset(self):
        staff_queryset = self.request.user.staff.exhibition.staff_set.exclude(id=self.request.user.staff.id)
        user_queryset = User.objects.filter(staff__in=staff_queryset)
        return user_queryset
