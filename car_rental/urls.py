from django.urls import path

from django.contrib.auth import views as auth_views
from car_rental import views

app_name = 'car_rental'
urlpatterns = [
    path('', views.home_view, name='home'),
    path('login/', auth_views.LoginView.as_view(template_name='car_rental/login.html'), name='login'),
    path('signup/', views.signup, name='signup'),
    path('requests/', views.RentRequestRenterListView.as_view(), name='requests_renter'),
    path('requests/staff/', views.RentRequestStaffListView.as_view(), name='requests_staff'),
    path('requests/answer/', views.answer_requests_view, name='answer_requests'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/<int:pk>/', views.UserDetailView.as_view(), name='user_info'),
    path('profile/password/', views.change_password, name='change_password'),
    path('profile/credit/', views.ChangeCreditView.as_view(), name='change_credit'),
    path('profile/logout/', views.logout_view, name='logout'),
    path('cars/', views.CarListRenterView.as_view(), name='cars'),
    path('cars/staff/', views.CarListStaffView.as_view(), name='cars_staff'),
    path('cars/add/', views.AddCarView.as_view(), name='add_car'),
    path('cars/<int:pk>/', views.CarDetailView.as_view(), name='car'),
    path('cars/<int:pk>/rent/', views.rent_request_view, name='rent_request'),
    path('cars/<int:pk>/edit/', views.EditCarView.as_view(), name='edit_car'),
    path('cars/<int:pk>/delete/', views.DeleteCarView.as_view(), name='delete_car'),
    path('cars/<int:pk>/repair/', views.NeedRepairCarView.as_view(), name='needs_repair'),
    path('staff/', views.StaffListView.as_view(), name='staff'),
    path('staff/add/', views.StaffCreateView.as_view(), name='add_staff'),
    path('staff/<int:pk>/', views.StaffDetailView.as_view(), name='staff_detail'),
    path('staff/<int:pk>/delete/', views.StaffDeleteView.as_view(), name='delete_staff'),
    path('staff/<int:pk>/perms/', views.ChangePermissions.as_view(), name='staff_perms')

]
