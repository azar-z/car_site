from django.contrib import messages
from django.contrib.auth import authenticate, login, update_session_auth_hash, logout
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.auth.models import Permission
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import generic
from django_filters import views as filter_views
from django_tables2.views import SingleTableMixin

from . import decorators
from . import filters as my_filters
from .forms import StaffCreationForm
from .models import Car, RentRequest, User, Exhibition, Staff
from . import forms as my_forms
from . import tables as my_tables


@method_decorator(decorators.user_is_not_staff, name='dispatch')
class CarListRenterView(filter_views.FilterView):
    template_name = 'car_rental/car_list.html'
    model = Car
    context_object_name = 'cars'
    filterset_class = my_filters.CarFilterSet

    def get_queryset(self):
        return Car.objects.exclude(rent_end_time__gt=timezone.now()).filter(needs_repair=False)


@method_decorator(decorators.user_is_staff, name='dispatch')
class CarListStaffView(SingleTableMixin, filter_views.FilterView):
    template_name = 'car_rental/car_list_staff.html'
    model = Car
    context_object_name = 'cars'
    paginate_by = 7
    filterset_class = my_filters.CarFilterSet
    table_class = my_tables.CarStaffTable

    def get_queryset(self):
        current_user = self.request.user
        return current_user.staff.exhibition.cars_owned.all()


class CarDetailView(generic.DetailView):
    model = Car
    context_object_name = 'car'
    template_name = 'car_rental/car_detail.html'

    def get_queryset(self):
        return Car.objects.all()


@login_required()
def rent_request_view(request, pk):
    car = get_object_or_404(Car, id=pk)
    if request.method == 'POST':
        form = my_forms.RentRequestForm(request.POST)
        if form.is_valid():
            rent_start_time = form.cleaned_data.get('rent_start_time')
            rent_end_time = form.cleaned_data.get('rent_end_time')
            rent_req = RentRequest.objects.create(car=car, requester=request.user, rent_end_time=rent_end_time,
                                                  rent_start_time=rent_start_time)
            rent_req.save()
            return HttpResponseRedirect(reverse('car_rental:requests_renter'))
    messages.error(request, 'Please enter valid start and end time.')
    return HttpResponseRedirect(reverse('car_rental:car', kwargs={'pk': pk}))


@method_decorator(login_required, name='dispatch')
@method_decorator(decorators.user_is_not_staff, name='dispatch')
class RentRequestRenterListView(SingleTableMixin, filter_views.FilterView):
    template_name = 'car_rental/request_list_renter.html'
    model = RentRequest
    context_object_name = 'requests'
    paginate_by = 7
    filterset_class = my_filters.RentRequestFilterSet
    table_class = my_tables.RentRequestRenterTable

    def get_queryset(self):
        current_user = self.request.user
        return current_user.rentrequest_set.all().order_by('-rent_start_time')


@method_decorator(login_required, name='dispatch')
@method_decorator(decorators.user_is_staff, name='dispatch')
class RentRequestStaffListView(PermissionRequiredMixin, generic.ListView):
    template_name = 'car_rental/request_list_staff.html'
    model = RentRequest
    context_object_name = 'requests'
    permission_required = 'car_rental.can_answer_request'

    def get_queryset(self):
        current_user = self.request.user
        return current_user.staff.exhibition.get_all_requests().order_by('rent_start_time').filter(has_result=False)


@login_required()
@decorators.user_is_staff
@permission_required('car_rental.can_answer_request', raise_exception=True)
def answer_requests_view(request):
    user = request.user
    if request.method == 'POST':
        unanswered_requests = user.staff.exhibition.get_all_requests().filter(has_result=False)
        for unanswered_request in unanswered_requests:
            try:
                answer = request.POST[str(unanswered_request.id)]
                if answer == 'yes':
                    if unanswered_request.car.is_rented():
                        messages.error(request,
                                       'Car ' + unanswered_request.car.car_type + ' is already rented.')
                        unanswered_request.reject(user)
                    else:
                        unanswered_request.accept(user)
                elif answer == 'no':
                    unanswered_request.reject(user)
                else:
                    pass
            except KeyError:
                pass
    return HttpResponseRedirect(reverse('car_rental:requests_staff'))


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
class ChangeCreditView(PermissionRequiredMixin, generic.FormView):
    template_name = 'car_rental/change_credit.html'
    form_class = my_forms.ChangeCreditForm
    permission_required = 'car_rental.can_access_credit'

    def form_valid(self, form):
        delta_credit = form.cleaned_data['delta_credit']
        current_user = self.request.user
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
            else:
                user.user_permissions.add(Permission.objects.get(codename='can_access_credit'))
            login(request, user)
            return HttpResponseRedirect(reverse('car_rental:home'))
    else:
        form = my_forms.SignUpForm()
    return render(request, 'car_rental/signup.html', {'form': form})


@method_decorator(login_required, name='dispatch')
@method_decorator(decorators.user_is_staff, name='dispatch')
class AddCarView(PermissionRequiredMixin, generic.CreateView):
    model = Car
    template_name = 'car_rental/add_car.html'
    fields = ['car_type', 'plate', 'price_per_hour', 'image']
    permission_required = 'car_rental.can_access_car'

    def form_valid(self, form):
        response = super(AddCarView, self).form_valid(form)
        current_user = User.objects.get(id=self.request.user.id)
        self.object.set_owner(current_user.staff.exhibition)
        return response


@method_decorator(login_required, name='dispatch')
@method_decorator(decorators.user_is_staff, name='dispatch')
class EditCarView(PermissionRequiredMixin, generic.UpdateView):
    model = Car
    template_name = 'car_rental/edit_car.html'
    fields = ['price_per_hour']
    permission_required = 'car_rental.can_access_car'

    def get_queryset(self):
        current_user = self.request.user
        return current_user.staff.exhibition.cars_owned.filter(rent_end_time__lte=timezone.now())


@method_decorator(login_required, name='dispatch')
class DeleteCarView(PermissionRequiredMixin, generic.DeleteView):
    model = Car
    template_name = 'car_rental/delete_car.html'
    permission_required = 'car_rental.can_access_car'

    def get_success_url(self):
        return reverse('car_rental:cars')

    def get_queryset(self):
        current_user = self.request.user
        return current_user.staff.exhibition.cars_owned.filter(rent_end_time__lte=timezone.now())


@method_decorator(login_required, name='dispatch')
class UserDetailView(PermissionRequiredMixin, generic.DetailView):
    model = User
    context_object_name = 'user'
    template_name = 'car_rental/user_info.html'
    permission_required = 'car_rental.can_answer_request'

    def get_queryset(self):
        current_user = self.request.user
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
        if car.renter == self.request.user:
            if car.needs_repair:
                car.renter.change_credit(-100)
                car.owner.change_credit(100)
            car.needs_repair = False
            car.save()
        return response

    def get_queryset(self):
        current_user = self.request.user
        if current_user.is_staff:
            return current_user.staff.exhibition.cars_owned.all()
        else:
            return current_user.cars_rented.filter(needs_repair=True)


@method_decorator(login_required, name='dispatch')
@method_decorator(decorators.user_is_staff, name='dispatch')
class StaffCreateView(PermissionRequiredMixin, generic.CreateView):
    model = User
    form_class = StaffCreationForm
    template_name = 'car_rental/add_staff.html'
    permission_required = 'car_rental.can_access_staff'

    def get_success_url(self):
        return reverse('car_rental:staff')

    def get_queryset(self):
        return User.objects.all()

    def form_valid(self, form):
        current_user = self.request.user
        response = super(StaffCreateView, self).form_valid(form)
        exhibition = current_user.staff.exhibition
        is_senior = False
        if form.cleaned_data.get('staff_type') == 'S':
            is_senior = True
        staff = Staff.objects.create(user=self.object, exhibition=exhibition, is_senior=is_senior)
        staff.save()
        return response


@method_decorator(login_required, name='dispatch')
@method_decorator(decorators.user_is_staff, name='dispatch')
class StaffListView(PermissionRequiredMixin, SingleTableMixin, filter_views.FilterView):
    model = Staff
    template_name = 'car_rental/staff_list.html'
    context_object_name = 'staff_list'
    paginate_by = 7
    permission_required = 'car_rental.can_access_staff'
    filterset_class = my_filters.StaffFilterSet
    table_class = my_tables.StaffTable

    def get_queryset(self):
        return self.request.user.staff.exhibition.staff_set.exclude(id=self.request.user.staff.id)


@method_decorator(login_required, name='dispatch')
@method_decorator(decorators.user_is_staff, name='dispatch')
class StaffDetailView(PermissionRequiredMixin, generic.DetailView):
    model = Staff
    template_name = 'car_rental/staff_detail.html'
    permission_required = 'car_rental.can_access_staff'

    def get_queryset(self):
        return self.request.user.staff.exhibition.staff_set.exclude(id=self.request.user.staff.id)


@method_decorator(login_required, name='dispatch')
@method_decorator(decorators.user_is_staff, name='dispatch')
class StaffDeleteView(PermissionRequiredMixin, generic.DeleteView):
    model = User
    template_name = 'car_rental/delete_staff.html'
    permission_required = 'car_rental.can_access_staff'

    def get_success_url(self):
        return reverse('car_rental:staff')

    def get_queryset(self):
        staff_queryset = self.request.user.staff.exhibition.staff_set.exclude(id=self.request.user.staff.id)
        user_queryset = User.objects.filter(staff__in=staff_queryset)
        return user_queryset


@method_decorator(login_required, name='dispatch')
@method_decorator(decorators.user_is_staff, name='dispatch')
class ChangePermissions(PermissionRequiredMixin, generic.UpdateView):
    model = Staff
    form_class = my_forms.StaffPermissionsForm
    template_name = 'car_rental/staff_permissions.html'
    permission_required = 'car_rental.can_access_staff'

    def form_valid(self, form):
        response = super(ChangePermissions, self).form_valid(form)
        perms = form.cleaned_data.get('perms')
        if 'CREDIT' in perms:
            self.object.add_permissions('can_access_credit')
        else:
            self.object.remove_permissions('can_access_credit')
        if 'REQUEST' in perms:
            self.object.add_permissions('can_answer_request')
        else:
            self.object.remove_permissions('can_answer_request')
        if 'CAR' in perms:
            self.object.add_permissions('can_access_car')
        else:
            self.object.remove_permissions('can_access_car')
        if 'STAFF' in perms:
            self.object.add_permissions('can_access_staff')
        else:
            self.object.remove_permissions('can_access_staff')
        return response
