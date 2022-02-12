from django.urls import path

from . import views
from .views import LoginView

app_name = 'car_rental'
urlpatterns = [
    path('', LoginView.as_view(), name='login'),
    path('cars', views.show_cars, name='cars'),

]
