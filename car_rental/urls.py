from django.urls import path

from . import views

app_name = 'car_rental'
urlpatterns = [
    path('', views.home_view, name='home'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('cars/', views.CarListView.as_view(), name='cars'),
    path('cars/<int:pk>/', views.CarDetailView.as_view(), name='car'),
    path('cars/<int:pk>/rent/', views.rent_request_view, name='rent_request'),
    path('requests/', views.RentRequestListView.as_view(), name='requests'),
    path('requests/answer/', views.answer_requests_view, name='answer_requests'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/password/', views.change_password, name='change_password'),
    path('profile/credit/', views.ChangeCreditView.as_view(), name='change_credit'),
    path('profile/logout/', views.logout_view, name='logout'),


]
