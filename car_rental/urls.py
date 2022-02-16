from django.urls import path

from . import views

app_name = 'car_rental'
urlpatterns = [
    path('', views.LoginView.as_view(), name='login'),
    path('cars/', views.CarListView.as_view(), name='cars'),
    path('cars/<int:pk>/', views.CarDetailView.as_view(), name='car'),
    path('cars/<int:pk>/rent/', views.rent_request_view, name='rent_request'),

]
