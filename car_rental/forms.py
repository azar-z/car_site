from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError

from car_rental.models import User


class LoginForm(forms.Form):
    username = forms.CharField(label='Username')
    password = forms.CharField(label='Password', widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
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
