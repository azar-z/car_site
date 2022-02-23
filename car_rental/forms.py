from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.utils import timezone

from car_rental.models import User


class LoginForm(forms.Form):
    username = forms.CharField(label='Username')
    password = forms.CharField(label='Password', widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super(LoginForm, self).clean()
        username = cleaned_data['username']
        password = cleaned_data['password']

        if username and password:
            user = authenticate(username=username, password=password)
            if (user is None) or (not user.is_active):
                raise ValidationError("Username and Password didn't match.")
        return cleaned_data


class ChangeCreditForm(forms.Form):
    delta_credit = forms.IntegerField(label='Delta Credit')


class SignUpForm(UserCreationForm):
    CHOICES = [('EX', 'Exhibition'),
               ('R', 'Renter')]

    user_type = forms.ChoiceField(choices=CHOICES, widget=forms.RadioSelect, label='Who are you?')

    class Meta:
        model = User
        fields = ('username', 'user_type', 'password1', 'password2', )


class StaffCreationForm(UserCreationForm):

    CHOICES = [('N', 'Normal'),
               ('S', 'Senior')]

    staff_type = forms.ChoiceField(choices=CHOICES, widget=forms.RadioSelect,
                                   label='What kind of staff are you adding?')

    class Meta:
        model = User
        fields = ('username', 'staff_type', 'password1', 'password2', )


class RentRequestForm(forms.Form):
    rent_start_time = forms.DateTimeField()
    rent_end_time = forms.DateTimeField()

    def clean(self):
        cleaned_data = super(RentRequestForm, self).clean()
        rent_start_time = cleaned_data['rent_start_time']
        rent_end_time = cleaned_data['rent_end_time']

        if rent_end_time and rent_end_time:
            if rent_end_time <= rent_start_time or rent_start_time < timezone.now():
                raise ValidationError("Request is not valid.")
        return cleaned_data
