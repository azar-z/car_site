from django import forms
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError


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
