import datetime

from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from car_rental.models import User, Car, RentRequest, Staff, Exhibition


def create_exhibition(name='ex1'):
    exhibition = Exhibition.objects.create(name="ex1")
    exhibition.save()
    return exhibition


def create_user(username=None, password='1111', is_staff=False, exhibition=None, ex_name='ex1'):
    if not username:
        username = username = 'Farhad' + str(User.objects.count())
    user = User.objects.create_user(username=username, password=password)
    user.save()
    if is_staff:
        if not exhibition:
            exhibition = create_exhibition(ex_name)
        staff = Staff.objects.create(user=user, exhibition=exhibition)
        staff.save()
    return user


class LoginViewTest(TestCase):
    def test_login_existing_activated_renter(self):
        username = 'Farhad'
        password = '1111'
        create_user(username, password)
        response = self.client.post(reverse('car_rental:login'), {'username': username, 'password': password})
        self.assertRedirects(response, reverse('car_rental:home'))

    def test_login_existing_activated_staff(self):
        username = 'Farhad'
        password = '1111'
        user = create_user(username, password, True)
        response = self.client.post(reverse('car_rental:login'), {'username': username, 'password': password})
        self.assertRedirects(response, reverse('car_rental:home'))

    def test_login_existing_not_activated_user(self):
        username = 'Farhad'
        password = '1111'
        data = {'username': username, 'password': password}
        user = create_user(username, password)
        user.is_active = False
        user.save()
        response = self.client.post(reverse('car_rental:login'), data)
        self.assertContains(response, "Please enter a correct username and password.")

    def test_login_not_existing_user(self):
        username = 'Farhad'
        password = '1111'
        data = {'username': username, 'password': password}
        response = self.client.post(reverse('car_rental:login'), data)
        self.assertContains(response, "Please enter a correct username and password.")


def login_a_user(client, user=None, username=None, password='1111', is_staff=False, exhibition=None, ex_name='ex1'):
    if not username:
        username = username = 'Farhad' + str(User.objects.count())
    if not user:
        user = create_user(username, password, is_staff, exhibition, ex_name)
    client.force_login(user)
    return user


def create_car(car_type='type1', owner=None, ex_name='ex1'):
    if not owner:
        user = create_user(is_staff=True, ex_name=ex_name)
        owner = user.staff.exhibition
    car = Car.objects.create(car_type=car_type, owner=owner)
    car.save()
    return car


def create_rented_car(car_type='type1', renter=None, owner=None, days=1, ex_name='ex1'):
    if not renter:
        renter = create_user('renter1')
    if not owner:
        staff_user = create_user(is_staff=True, ex_name=ex_name)
        owner = staff_user.staff.exhibition
    car = create_car(car_type, owner, ex_name)
    car.rent_end_time = timezone.now() + datetime.timedelta(days=days)
    car.renter = renter
    car.owner = owner
    car.save()
    return car


class CarListViewTest(TestCase):

    def test_not_login(self):
        car = create_car()
        response = self.client.get(reverse('car_rental:cars'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, car.car_type)

    def test_no_car_exists(self):
        login_a_user(self.client)
        response = self.client.get(reverse('car_rental:cars'))
        self.assertContains(response, 'Available Cars')
        self.assertContains(response, "There are no available cars for you!")

    def test_no_car_exists_staff(self):
        staff_user = login_a_user(self.client, is_staff=True)
        car = create_car(ex_name='ex2')
        response = self.client.get(reverse('car_rental:cars'))
        self.assertContains(response, 'Your Cars')
        self.assertContains(response, "You have no cars!")
        self.assertNotContains(response, car.car_type)
        self.assertNotContains(response, 'Status')

    def test_not_show_rented_car(self):
        login_a_user(self.client)
        car = create_rented_car()
        response = self.client.get(reverse('car_rental:cars'))
        self.assertContains(response, 'Available Cars')
        self.assertContains(response, "There are no available cars for you!")
        self.assertNotContains(response, car.car_type)

    def test_show_available_car(self):
        login_a_user(self.client)
        car = create_car()
        response = self.client.get(reverse('car_rental:cars'))
        self.assertContains(response, 'Available Cars')
        self.assertNotContains(response, "There are no available cars for you!")
        self.assertContains(response, car.car_type)

    def test_show_not_rented_car_to_staff(self):
        staff_user = login_a_user(self.client, is_staff=True)
        car = create_car(owner=staff_user.staff.exhibition)
        response = self.client.get(reverse('car_rental:cars'))
        self.assertContains(response, 'Your Cars')
        self.assertNotContains(response, "You have no cars!")
        self.assertContains(response, car.car_type)
        self.assertContains(response, car.id)
        self.assertContains(response, 'free')
        self.assertContains(response, 'Status')

    def test_show_rented_car_to_staff(self):
        staff_user = login_a_user(self.client, is_staff=True)
        owner = staff_user.staff.exhibition
        car = create_rented_car(owner=owner)
        response = self.client.get(reverse('car_rental:cars'))
        self.assertContains(response, 'Your Cars')
        self.assertNotContains(response, "You have no cars!")
        self.assertContains(response, car.car_type)
        self.assertContains(response, car.id)
        self.assertContains(response, 'rented')
        self.assertContains(response, 'Status')

    def test_not_show_need_repair_car(self):
        login_a_user(self.client)
        car = create_car()
        car.needs_repair = True
        car.save()
        response = self.client.get(reverse('car_rental:cars'))
        self.assertContains(response, 'Available Cars')
        self.assertContains(response, "There are no available cars for you!")
        self.assertNotContains(response, car.car_type)


class CarDetailTest(TestCase):

    def test_not_login(self):
        car = create_car()
        response = self.client.get(reverse('car_rental:car', kwargs={'pk': 1}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, car.car_type)

    def test_no_car_with_this_id(self):
        login_a_user(self.client)
        response = self.client.get(reverse('car_rental:car', kwargs={'pk': 1}))
        self.assertEqual(response.status_code, 404)

    def test_rented_car(self):
        login_a_user(self.client)
        car = create_rented_car()
        response = self.client.get(reverse('car_rental:car', kwargs={'pk': 1}))
        self.assertContains(response, car.car_type)
        self.assertContains(response, 'rented')
        self.assertNotContains(response, 'Want to rent this car?')
        self.assertContains(response, 'till')
        self.assertContains(response, car.rent_end_time.year)
        self.assertContains(response, car.rent_end_time.day)
        self.assertNotContains(response, 'from')
        self.assertNotContains(response, car.renter.username)
        self.assertContains(response, car.owner.name)

    def test_not_rented_car(self):
        login_a_user(self.client)
        car = create_car()
        response = self.client.get(reverse('car_rental:car', kwargs={'pk': 1}))
        self.assertContains(response, car.car_type)
        self.assertContains(response, 'free')
        self.assertContains(response, 'Want to rent this car?')
        self.assertNotContains(response, 'from')
        self.assertNotContains(response, 'till')

    def test_rented_car_by_renter(self):
        renter = login_a_user(self.client)
        car = create_rented_car(renter=renter)
        response = self.client.get(reverse('car_rental:car', kwargs={'pk': 1}))
        self.assertContains(response, car.car_type)
        self.assertContains(response, 'is rented by you')
        self.assertNotContains(response, 'Want to rent this car?')
        self.assertContains(response, 'till')
        self.assertContains(response, car.rent_end_time.year)
        self.assertContains(response, car.rent_end_time.day)
        self.assertContains(response, 'from')
        self.assertContains(response, car.rent_start_time.year)
        self.assertContains(response, car.rent_start_time.day)
        self.assertContains(response, car.owner.name)

    def test_rented_car_by_staff(self):
        staff_user = login_a_user(self.client, is_staff=True)
        staff_user.staff.add_permissions('can_access_car')
        owner = staff_user.staff.exhibition
        car = create_rented_car(owner=owner)
        response = self.client.get(reverse('car_rental:car', kwargs={'pk': 1}))
        self.assertContains(response, car.car_type)
        self.assertContains(response, 'rented')
        self.assertContains(response, 'Status')
        self.assertNotContains(response, 'Want to rent this car?')
        self.assertContains(response, 'till')
        self.assertContains(response, car.rent_end_time.year)
        self.assertContains(response, car.rent_end_time.day)
        self.assertContains(response, 'from')
        self.assertContains(response, car.rent_start_time.year)
        self.assertContains(response, car.rent_start_time.day)
        self.assertContains(response, car.renter.username)
        self.assertContains(response, 'Needs Repair?')
        self.assertNotContains(response, 'Change Price')
        self.assertNotContains(response, 'Remove')

    def test_not_rented_car_by_staff(self):
        staff_user = login_a_user(self.client, is_staff=True)
        staff_user.staff.add_permissions('can_access_car')
        owner = staff_user.staff.exhibition
        car = create_car(owner=owner)
        response = self.client.get(reverse('car_rental:car', kwargs={'pk': 1}))
        self.assertContains(response, car.car_type)
        self.assertContains(response, 'free')
        self.assertContains(response, 'Status')
        self.assertNotContains(response, 'Want to rent this car?')
        self.assertContains(response, 'Needs Repair?')
        self.assertContains(response, 'Change Price')
        self.assertContains(response, 'Remove')


    def test_staff_car_permission_not_given(self):
        staff_user = login_a_user(self.client, is_staff=True)
        owner = staff_user.staff.exhibition
        car = create_car(owner=owner)
        response = self.client.get(reverse('car_rental:car', kwargs={'pk': 1}))
        self.assertContains(response, car.car_type)
        self.assertNotContains(response, 'Needs Repair?')
        self.assertNotContains(response, 'Change Price')
        self.assertNotContains(response, 'Remove')

    def test_car_needs_repair(self):
        login_a_user(self.client)
        car = create_rented_car()
        car.needs_repair = True
        car.save()
        response = self.client.get(reverse('car_rental:car', kwargs={'pk': 1}))
        self.assertContains(response, 'This car needs repair!')
        self.assertNotContains(response, 'This car is free to rent!')
        self.assertNotContains(response, 'Want to rent this car?')

    def test_car_needs_repair_by_renter(self):
        user = login_a_user(self.client)
        car = create_rented_car(renter=user)
        car.needs_repair = True
        car.save()
        response = self.client.get(reverse('car_rental:car', kwargs={'pk': 1}))
        self.assertContains(response, 'This car needs repair!')
        self.assertNotContains(response, 'This car is free to rent!')
        self.assertNotContains(response, 'Want to rent this car?')
        self.assertContains(response, 'Confirm it needs repair')


def create_request(requester, car, start_time=timezone.now(), end_time=timezone.now() + datetime.timedelta(days=1)):
    rent_request = RentRequest.objects.create(requester=requester, car=car, rent_start_time=start_time,
                                              rent_end_time=end_time)
    rent_request.save()
    return rent_request


class RentRequestListViewTest(TestCase):

    def test_not_login(self):
        create_car()
        response = self.client.get(reverse('car_rental:requests'))
        self.assertRedirects(response,
                             reverse('car_rental:login') + "?next=" + reverse('car_rental:requests'))

    def test_exhibition_no_request(self):
        staff_user = login_a_user(self.client, is_staff=True)
        owner = staff_user.staff.exhibition
        create_car(owner=owner)
        response = self.client.get(reverse('car_rental:requests'))
        self.assertContains(response, "No Requests")
        self.assertNotContains(response, "Please accept or reject these requests:")

    def test_exhibition_with_unanswered_result(self):
        staff_user = login_a_user(self.client, is_staff=True)
        owner = staff_user.staff.exhibition
        car = create_car(owner=owner)
        requester = create_user('user1')
        create_request(requester, car)
        response = self.client.get(reverse('car_rental:requests'))
        self.assertNotContains(response, "No Requests")
        self.assertContains(response, "Please accept or reject these requests:")
        self.assertContains(response, car.car_type)
        self.assertContains(response, car.plate)
        self.assertContains(response, requester.username)

    def test_exhibition_with_answered_result(self):
        staff_user = login_a_user(self.client, is_staff=True)
        owner = staff_user.staff.exhibition
        car = create_car(owner=owner)
        requester = create_user('user1')
        rent_request = create_request(requester, car)
        rent_request.has_result = True
        rent_request.save()
        response = self.client.get(reverse('car_rental:requests'))
        self.assertNotContains(response, "Please accept or reject these requests:")
        self.assertContains(response, "No Requests")
        self.assertNotContains(response, car.car_type)

    def test_renter_with_no_result(self):
        staff_user = login_a_user(self.client, is_staff=True)
        owner = staff_user.staff.exhibition
        car = create_car(owner=owner)
        response = self.client.get(reverse('car_rental:requests'))
        self.assertContains(response, "No Requests")
        self.assertNotContains(response, "Please accept or reject these requests:")

    def test_renter_with_unanswered_result(self):
        staff_user = create_user(is_staff=True)
        owner = staff_user.staff.exhibition
        car = create_car(owner=owner)
        requester = login_a_user(self.client)
        create_request(requester, car)
        response = self.client.get(reverse('car_rental:requests'))
        self.assertNotContains(response, "No Requests")
        self.assertNotContains(response, "Please accept or reject these requests:")
        self.assertContains(response, car.car_type)
        self.assertContains(response, car.owner.name)
        self.assertContains(response, "Not determined yet")

    def test_renter_with_accepted_result(self):
        staff_user = create_user(is_staff=True)
        owner = staff_user.staff.exhibition
        car = create_car(owner=owner)
        requester = login_a_user(self.client)
        rent_request = create_request(requester, car)
        rent_request.has_result = True
        rent_request.is_accepted = True
        rent_request.save()
        response = self.client.get(reverse('car_rental:requests'))
        self.assertNotContains(response, "No Requests")
        self.assertNotContains(response, "Please accept or reject these requests:")
        self.assertContains(response, car.car_type)
        self.assertContains(response, owner.name)
        self.assertContains(response, "Accepted")

    def test_renter_with_rejected_result(self):
        staff_user = create_user(is_staff=True)
        owner = staff_user.staff.exhibition
        car = create_car(owner=owner)
        requester = login_a_user(self.client)
        rent_request = create_request(requester, car)
        rent_request.has_result = True
        rent_request.is_accepted = False
        rent_request.save()
        response = self.client.get(reverse('car_rental:requests'))
        self.assertNotContains(response, "No Requests")
        self.assertNotContains(response, "Please accept or reject these requests:")
        self.assertContains(response, car.car_type)
        self.assertContains(response, owner.name)
        self.assertContains(response, "Rejected")


class AnswerRequestView(TestCase):

    def test_not_login(self):
        response = self.client.post(reverse('car_rental:answer_requests'))
        self.assertRedirects(response, reverse('car_rental:login') + "?next=" + reverse('car_rental:answer_requests'))

    def test_not_exhibition_user(self):
        user = login_a_user(self.client)
        response = self.client.get(reverse('car_rental:answer_requests'))
        self.assertEqual(response.status_code, 403)


    def test_no_request_permission(self):
        staff_user = login_a_user(self.client, is_staff=True)
        owner = staff_user.staff.exhibition
        car = create_car(owner=owner)
        car.price_per_hour = 100
        car.save()
        requester = create_user('user1')
        rent_request = create_request(requester, car, timezone.now(), timezone.now() + datetime.timedelta(hours=10))
        response = self.client.post(reverse('car_rental:answer_requests'), {'1': 'no'})
        self.assertEqual(response.status_code, 403)


    def test_not_answered_request(self):
        staff_user = login_a_user(self.client, is_staff=True)
        staff_user.staff.add_permissions('can_answer_request')
        owner = staff_user.staff.exhibition
        car = create_car(owner=owner)
        requester = create_user('user1')
        rent_request = create_request(requester, car)
        response = self.client.get(reverse('car_rental:answer_requests'))
        self.assertRedirects(response, reverse('car_rental:requests'))
        self.assertFalse(rent_request.has_result)
        self.assertEqual(owner.credit, 0)
        self.assertEqual(requester.credit, 0)

    def test_rejected_request(self):
        staff_user = login_a_user(self.client, is_staff=True)
        staff_user.staff.add_permissions('can_answer_request')
        owner = staff_user.staff.exhibition
        car = create_car(owner=owner)
        car.price_per_hour = 100
        car.save()
        requester = create_user('user1')
        rent_request = create_request(requester, car, timezone.now(), timezone.now() + datetime.timedelta(hours=10))
        response = self.client.post(reverse('car_rental:answer_requests'), {'1': 'no'})
        rent_request.refresh_from_db()
        owner.refresh_from_db()
        requester.refresh_from_db()
        self.assertRedirects(response, reverse('car_rental:requests'))
        self.assertTrue(rent_request.has_result)
        self.assertFalse(rent_request.is_accepted)
        self.assertEqual(owner.credit, 0)
        self.assertEqual(requester.credit, 0)

    def test_accepted_request(self):
        staff_user = login_a_user(self.client, is_staff=True)
        staff_user.staff.add_permissions('can_answer_request')
        owner = staff_user.staff.exhibition
        car = create_car(owner=owner)
        car.price_per_hour = 100
        car.save()
        requester = create_user('user1')
        rent_request = create_request(requester, car, timezone.now(), timezone.now() + datetime.timedelta(hours=10))
        response = self.client.post(reverse('car_rental:answer_requests'), {'1': 'yes'})
        rent_request.refresh_from_db()
        owner.refresh_from_db()
        requester.refresh_from_db()
        self.assertRedirects(response, reverse('car_rental:requests'))
        self.assertTrue(rent_request.has_result)
        self.assertTrue(rent_request.is_accepted)
        self.assertEqual(owner.credit, 1000)
        self.assertEqual(requester.credit, -1000)


class ProfileViewTest(TestCase):

    def test_not_login(self):
        response = self.client.get(reverse('car_rental:profile'))
        self.assertRedirects(response, reverse('car_rental:login') + "?next=" + reverse('car_rental:profile'))

    def test_no_credit_permission_staff(self):
        staff_user = login_a_user(self.client, is_staff=True)
        exhibition = staff_user.staff.exhibition
        response = self.client.get(reverse('car_rental:profile'))
        self.assertContains(response, staff_user.username)
        self.assertContains(response, "Exhibition Staff")
        self.assertContains(response, 'Exhibition')
        self.assertContains(response, exhibition.name)
        self.assertContains(response, 'Exhibition ID')
        self.assertContains(response, 'Change Password')
        self.assertNotContains(response, 'Change Credit')
        self.assertNotContains(response, 'Exhibition Credit')

    def test_credit_permission_staff(self):
        staff_user = login_a_user(self.client, is_staff=True)
        staff_user.staff.add_permissions('can_access_credit')
        exhibition = staff_user.staff.exhibition
        exhibition.credit = 2535
        exhibition.save()
        response = self.client.get(reverse('car_rental:profile'))
        self.assertContains(response, staff_user.username)
        self.assertContains(response, "Exhibition Staff")
        self.assertContains(response, exhibition.name)
        self.assertContains(response, 'Exhibition ID')
        self.assertContains(response, 'User ID')
        self.assertContains(response, 'Change Password')
        self.assertContains(response, 'Change Credit')
        self.assertContains(response, 'Exhibition Credit')
        self.assertContains(response, '2535')

    def test_renter(self):
        renter = login_a_user(self.client)
        permission = Permission.objects.get(codename='can_access_credit')
        renter.user_permissions.add(permission)
        response = self.client.get(reverse('car_rental:profile'))
        self.assertContains(response, renter.username)
        self.assertContains(response, 'Renter')
        self.assertContains(response, 'Change Password')
        self.assertContains(response, 'Change Credit')


class PasswordChangeViewTest(TestCase):

    def test_invalid_password(self):
        login_a_user(self.client)
        response = self.client.post(reverse('car_rental:change_password'),
                                    {'old_password': '1111', 'new_password1': '1234', 'new_password2': '1234'},
                                    follow=True)
        self.assertContains(response, 'This password is too short.')

    def test_wrong_old_password(self):
        login_a_user(self.client)
        data = {'old_password': '2222', 'new_password1': '1234qsvg00', 'new_password2': '1234qsvg00'}
        response = self.client.post(reverse('car_rental:change_password'), data, follow=True)
        self.assertContains(response, 'Your old password was entered incorrectly. Please enter it again.')

    def test_valid_password_wrong_confirmation(self):
        login_a_user(self.client)
        response = self.client.post(reverse('car_rental:change_password'),
                                    {'old_password': '1111', 'new_password1': '1234qsvg00',
                                     'new_password2': '1234qsvg'}, follow=True)
        self.assertContains(response, 'The two password fields didn’t match.')

    def test_successful_password_change(self):
        user = login_a_user(self.client)
        data = {'old_password': '1111', 'new_password1': '1234qsvg00', 'new_password2': '1234qsvg00'}
        response = self.client.post(reverse('car_rental:change_password'), data, follow=True)
        user.refresh_from_db()
        self.assertTrue(user.check_password('1234qsvg00'))
        self.assertRedirects(response, reverse('car_rental:profile'))


class CreditChangeViewTest(TestCase):

    def test_changes_correctly(self):
        user = login_a_user(self.client)
        permission = Permission.objects.get(codename='can_access_credit')
        user.user_permissions.add(permission)
        self.assertEqual(user.credit, 0)
        response = self.client.post(reverse('car_rental:change_credit'), {'delta_credit': 100}, follow=True)
        user.refresh_from_db()
        self.assertTrue(user.credit, 100)
        self.assertRedirects(response, reverse('car_rental:profile'))

    def test_changes_correctly_for_permission_credit_staff(self):
        staff_user = login_a_user(self.client, is_staff=True)
        exhibition = staff_user.staff.exhibition
        staff_user.staff.add_permissions('can_access_credit')
        self.assertEqual(exhibition.credit, 0)
        self.assertEqual(staff_user.credit, 0)
        response = self.client.post(reverse('car_rental:change_credit'), {'delta_credit': 100}, follow=True)
        staff_user.refresh_from_db()
        exhibition.refresh_from_db()
        self.assertEqual(staff_user.credit, 0)
        self.assertEqual(exhibition.credit, 100)
        self.assertRedirects(response, reverse('car_rental:profile'))

    def test_permission_denied_for_no_credit_permission_staff(self):
        staff_user = login_a_user(self.client, is_staff=True)
        exhibition = staff_user.staff.exhibition
        self.assertEqual(exhibition.credit, 0)
        self.assertEqual(staff_user.credit, 0)
        response = self.client.post(reverse('car_rental:change_credit'), {'delta_credit': 100}, follow=True)
        staff_user.refresh_from_db()
        exhibition.refresh_from_db()
        self.assertEqual(staff_user.credit, 0)
        self.assertEqual(exhibition.credit, 0)
        self.assertEqual(response.status_code, 403)


class LogoutViewTest(TestCase):

    def test_logout_successfully(self):
        login_a_user(self.client)
        response = self.client.get(reverse('car_rental:logout'), follow=True)
        self.assertTrue(response.wsgi_request.user.is_anonymous)
        self.assertRedirects(response, reverse('car_rental:home'))


class AddCarViewTest(TestCase):

    def test_successful_car_add_for_car_permission_staff(self):
        staff_user = login_a_user(self.client, is_staff=True)
        staff_user.staff.add_permissions('can_access_car')
        exhibition = staff_user.staff.exhibition
        response = self.client.post(reverse('car_rental:add_car'),
                                    {'car_type': 'type1', 'plate': '1234', 'price_per_hour': '100'}, follow=True)
        exhibition.refresh_from_db()
        self.assertRedirects(response, reverse('car_rental:car', kwargs={'pk': '1'}))
        self.assertEqual(exhibition.cars_owned.get(id=1).car_type, 'type1')

    def test_access_denied_for_not_car_permission_staff(self):
        staff_user = login_a_user(self.client, is_staff=True)
        exhibition = staff_user.staff.exhibition
        response = self.client.post(reverse('car_rental:add_car'),
                                    {'car_type': 'type1', 'plate': '1234', 'price_per_hour': '100'}, follow=True)
        self.assertEqual(response.status_code, 403)

    def test_non_exhibition(self):
        login_a_user(self.client)
        response = self.client.post(reverse('car_rental:add_car'),
                                    {'car_type': 'type1', 'plate': '1234', 'price_per_hour': '100'}, follow=True)
        self.assertEqual(response.status_code, 403)


class EditCarTest(TestCase):

    def test_edit_price_successfully_with_car_permission(self):
        staff_user = login_a_user(self.client, is_staff=True)
        staff_user.staff.add_permissions('can_access_car')
        owner = staff_user.staff.exhibition
        car = create_car(owner=owner)
        car.price_per_hour = 10
        car.save()
        response = self.client.post(reverse('car_rental:edit_car', kwargs={'pk': '1'}), {'price_per_hour': 100})
        car.refresh_from_db()
        self.assertEqual(car.price_per_hour, 100)
        self.assertRedirects(response, reverse('car_rental:car', kwargs={'pk': '1'}))

    def test_access_denied_with_no_car_permission(self):
        staff_user = login_a_user(self.client, is_staff=True)
        owner = staff_user.staff.exhibition
        car = create_car(owner=owner)
        car.price_per_hour = 10
        car.save()
        response = self.client.post(reverse('car_rental:edit_car', kwargs={'pk': '1'}), {'price_per_hour': 100})
        self.assertEqual(response.status_code, 403)

    def test_non_exhibition(self):
        renter = login_a_user(self.client)
        car = create_car()
        car.price_per_hour = 10
        car.save()
        response = self.client.post(reverse('car_rental:edit_car', kwargs={'pk': '1'}), {'price_per_hour': 100})
        car.refresh_from_db()
        self.assertEqual(car.price_per_hour, 10)
        self.assertEqual(response.status_code, 403)

    def test_non_owner_exhibition(self):
        non_owner = login_a_user(self.client, is_staff=True)
        non_owner.staff.add_permissions('can_access_car')
        owner_staff_user = create_user(is_staff=True)
        owner = owner_staff_user.staff.exhibition
        car = create_car(owner=owner)
        car.price_per_hour = 10
        car.save()
        response = self.client.post(reverse('car_rental:edit_car', kwargs={'pk': '1'}), {'price_per_hour': 100})
        car.refresh_from_db()
        self.assertEqual(car.price_per_hour, 10)
        self.assertEqual(response.status_code, 404)

    def test_rented_car(self):
        staff_user = login_a_user(self.client, is_staff=True)
        staff_user.staff.add_permissions('can_access_car')
        owner = staff_user.staff.exhibition
        car = create_rented_car(owner=owner)
        car.price_per_hour = 10
        car.save()
        response = self.client.post(reverse('car_rental:edit_car', kwargs={'pk': '1'}), {'price_per_hour': 100})
        car.refresh_from_db()
        self.assertEqual(car.price_per_hour, 10)
        self.assertEqual(response.status_code, 404)


class NeedRepairViewTest(TestCase):

    def test_non_exhibition_not_need_repair(self):
        login_a_user(self.client)
        car = create_car()
        response = self.client.post(reverse('car_rental:needs_repair', kwargs={'pk': '1'}), {'needs_repair': True})
        car.refresh_from_db()
        self.assertEqual(response.status_code, 404)
        self.assertFalse(car.needs_repair)

    def test_non_owner_exhibition(self):
        non_owner = login_a_user(self.client, is_staff=True)
        staff_user = create_user(is_staff=True)
        car = create_car(owner=staff_user.staff.exhibition)
        car.needs_repair = False
        car.save()
        response = self.client.post(reverse('car_rental:needs_repair', kwargs={'pk': '1'}), {'needs_repair': True})
        car.refresh_from_db()
        self.assertEqual(response.status_code, 404)
        self.assertFalse(car.needs_repair)

    def test_successful_staff_need_repair(self):
        staff_user = login_a_user(self.client, is_staff=True)
        owner = staff_user.staff.exhibition
        car = create_car(owner=owner)
        response = self.client.post(reverse('car_rental:needs_repair', kwargs={'pk': '1'}), {'needs_repair': True})
        car.refresh_from_db()
        owner.refresh_from_db()
        self.assertTrue(car.needs_repair)
        self.assertEqual(owner.credit, 0)

    def test_successful_renter_need_repair(self):
        staff_user = create_user(is_staff=True)
        owner = staff_user.staff.exhibition
        renter = login_a_user(self.client)
        car = create_car(owner=owner)
        car.needs_repair = True
        car.renter = renter
        car.save()
        response = self.client.post(reverse('car_rental:needs_repair', kwargs={'pk': '1'}), {'needs_repair': True})
        car.refresh_from_db()
        renter.refresh_from_db()
        owner.refresh_from_db()
        self.assertFalse(car.needs_repair)
        self.assertEqual(owner.credit, 100)
        self.assertEqual(renter.credit, -100)

    def test_staff_not_need_repair_renter_need_repair(self):
        staff_user = create_user(is_staff=True)
        owner = staff_user.staff.exhibition
        renter = login_a_user(self.client)
        car = create_car(owner=owner)
        car.renter = renter
        car.save()
        response = self.client.post(reverse('car_rental:needs_repair', kwargs={'pk': '1'}), {'needs_repair': True})
        car.refresh_from_db()
        renter.refresh_from_db()
        owner.refresh_from_db()
        self.assertEqual(response.status_code, 404)
        self.assertFalse(car.needs_repair)
        self.assertEqual(owner.credit, 0)
        self.assertEqual(renter.credit, 0)

    def test_staff_need_repair_renter_not_need_repair(self):
        staff_user = create_user(is_staff=True)
        owner = staff_user.staff.exhibition
        renter = login_a_user(self.client)
        car = create_car(owner=owner)
        car.needs_repair = True
        car.renter = renter
        car.save()
        response = self.client.post(reverse('car_rental:needs_repair', kwargs={'pk': '1'}), {'needs_repair': False})
        car.refresh_from_db()
        renter.refresh_from_db()
        owner.refresh_from_db()
        self.assertFalse(car.needs_repair)
        self.assertEqual(owner.credit, 0)
        self.assertEqual(renter.credit, 0)
        self.assertEqual(response.status_code, 302)


class UserDetailViewTest(TestCase):

    def test_not_requested_user(self):
        user1 = login_a_user(self.client)
        user2 = create_user('user2')
        response = self.client.get(reverse('car_rental:user_info', kwargs={'pk': 2}))
        self.assertEqual(response.status_code, 403)

    def test_requested_user(self):
        staff_user = login_a_user(self.client, is_staff=True)
        staff_user.staff.add_permissions('can_answer_request')
        owner = staff_user.staff.exhibition
        user2 = create_user('user2')
        car = create_car(owner=owner)
        request = create_request(user2, car)
        response = self.client.get(reverse('car_rental:user_info', kwargs={'pk': 2}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, user2.username)
        self.assertContains(response, user2.id)
        self.assertContains(response, 'Renter')


class SignupViewTest(TestCase):

    def test_passwords_not_equal(self):
        data = {'username': 'user1', 'password1': 'qw12er34ty56', 'password2': 'eqw12er34ty56', 'user_type': 'R'}
        response = self.client.post(reverse('car_rental:signup'), data)
        self.assertContains(response, 'The two password fields didn’t match.')

    def test_not_unique_username(self):
        user = create_user('user1')
        data = {'username': 'user1', 'password1': 'qw12er34ty56', 'password2': 'qw12er34ty56', 'user_type': "R"}
        response = self.client.post(reverse('car_rental:signup'), data)
        self.assertContains(response, 'already exists')

    def test_successful_renter(self):
        data = {'username': 'user1', 'password1': 'qw12er34ty56', 'password2': 'qw12er34ty56', 'user_type': 'R'}
        response = self.client.post(reverse('car_rental:signup'), data)
        self.assertRedirects(response, reverse('car_rental:home'))
        user = User.objects.get(id=1)
        self.assertEqual(user.username, 'user1')
        self.assertEqual(user.is_staff, False)

    def test_successful_senior_staff(self):
        data = {'username': 'user1', 'password1': 'qw12er34ty56', 'password2': 'qw12er34ty56', 'user_type': 'EX'}
        response = self.client.post(reverse('car_rental:signup'), data)
        self.assertRedirects(response, reverse('car_rental:home'))
        user = User.objects.get(id=1)
        self.assertEqual(user.username, 'user1')
        self.assertEqual(user.is_staff, True)
        self.assertEqual(user.staff.is_senior, True)


class CreateStaffViewTest(TestCase):

    def test_not_staff_user(self):
        login_a_user(self.client)
        data = {'username': 'user2', 'password1': 'qw12er34', 'password2': 'qw12er34'}
        response = self.client.post(reverse('car_rental:add_staff'), data)
        self.assertEqual(response.status_code, 403)

    def test_not_staff_access_staff(self):
        login_a_user(self.client, is_staff=True)
        data = {'username': 'user2', 'password1': 'qw12er34', 'password2': 'qw12er34'}
        response = self.client.post(reverse('car_rental:add_staff'), data)
        self.assertEqual(response.status_code, 403)

    def test_different_passwords(self):
        staff_user = login_a_user(self.client, is_staff=True)
        staff_user.staff.add_permissions('can_access_staff')
        data = {'username': 'user2', 'password1': 'qw12er34', 'password2': 'eeqw12er34'}
        response = self.client.post(reverse('car_rental:add_staff'), data)
        self.assertNotEqual(response.status_code, 403)
        self.assertContains(response, 'The two password fields didn’t match.')

    def test_same_username(self):
        staff_user = login_a_user(self.client, is_staff=True)
        staff_user.staff.add_permissions('can_access_staff')
        data = {'username': staff_user.username, 'password1': 'qw12er34', 'password2': 'qw12er34'}
        response = self.client.post(reverse('car_rental:add_staff'), data)
        self.assertContains(response, 'already exists')

    def test_successful_normal_staff(self):
        staff_user = login_a_user(self.client, is_staff=True)
        staff_user.staff.add_permissions('can_access_staff')
        data = {'username': 'normal1', 'password1': 'qw12er34', 'password2': 'qw12er34'
            , 'staff_type': 'N'}
        response = self.client.post(reverse('car_rental:add_staff'), data)
        staff_user.refresh_from_db()
        new_staff = staff_user.staff.exhibition.staff_set.get(user__username='normal1')
        self.assertRedirects(response, reverse('car_rental:staff'))
        self.assertFalse(new_staff.is_senior)

    def test_successful_senior_staff(self):
        staff_user = login_a_user(self.client, is_staff=True)
        staff_user.staff.add_permissions('can_access_staff')
        data = {'username': 'senior1', 'password1': 'qw12er34', 'password2': 'qw12er34'
            , 'staff_type': 'S'}
        response = self.client.post(reverse('car_rental:add_staff'), data)
        staff_user.refresh_from_db()
        new_staff = staff_user.staff.exhibition.staff_set.get(user__username='senior1')
        self.assertRedirects(response, reverse('car_rental:staff'))
        self.assertTrue(new_staff.is_senior)


class StaffListViewTest(TestCase):

    def test_not_staff(self):
        user = login_a_user(self.client)
        response = self.client.get(reverse('car_rental:staff'))
        self.assertEqual(response.status_code, 403)

    def test_no_staff_permission(self):
        user = login_a_user(self.client, is_staff=True)
        response = self.client.get(reverse('car_rental:staff'))
        self.assertEqual(response.status_code, 403)

    def test_no_staffs(self):
        user = login_a_user(self.client, is_staff=True)
        user.staff.add_permissions('can_access_staff')
        response = self.client.get(reverse('car_rental:staff'))
        self.assertContains(response, 'You have no staffs.')

    def test_one_normal_staff(self):
        staff_user = login_a_user(self.client, is_staff=True)
        staff_user.staff.add_permissions('can_access_staff')
        staff_user = create_user(is_staff=True, exhibition=staff_user.staff.exhibition)
        response = self.client.get(reverse('car_rental:staff'))
        self.assertNotContains(response, 'You have no staffs.')
        self.assertContains(response, staff_user.username)
        self.assertContains(response, "Normal")

    def test_one_senior_staff(self):
        staff_user = login_a_user(self.client, is_staff=True)
        staff_user.staff.add_permissions('can_access_staff')
        staff_user = create_user(is_staff=True, exhibition=staff_user.staff.exhibition)
        staff_user.staff.is_senior = True
        staff_user.staff.save()
        response = self.client.get(reverse('car_rental:staff'))
        self.assertNotContains(response, 'You have no staffs.')
        self.assertContains(response, staff_user.username)
        self.assertContains(response, "Senior")


class StaffDetailViewTest(TestCase):

    def test_not_staff(self):
        user = login_a_user(self.client)
        response = self.client.get(reverse('car_rental:staff_detail', kwargs={'pk': 1}))
        self.assertEqual(response.status_code, 403)

    def test_access_denied(self):
        user = login_a_user(self.client, is_staff=True)
        response = self.client.get(reverse('car_rental:staff_detail', kwargs={'pk': 1}))
        self.assertEqual(response.status_code, 403)

    def test_no_staffs(self):
        user = login_a_user(self.client, is_staff=True)
        user.staff.add_permissions('can_access_staff')
        response = self.client.get(reverse('car_rental:staff_detail', kwargs={'pk': 2}))
        self.assertEqual(response.status_code, 404)

    def test_normal_staff(self):
        staff_user = login_a_user(self.client, is_staff=True)
        staff_user.staff.add_permissions('can_access_staff')
        staff_user = create_user(is_staff=True, exhibition=staff_user.staff.exhibition)
        response = self.client.get(reverse('car_rental:staff_detail', kwargs={'pk': 2}))
        self.assertNotContains(response, 'You have no staffs.')
        self.assertContains(response, staff_user.username)
        self.assertContains(response, "Normal")

    def test_senior_staff(self):
        staff_user = login_a_user(self.client, is_staff=True)
        staff_user.staff.add_permissions('can_access_staff')
        staff_user = create_user(is_staff=True, exhibition=staff_user.staff.exhibition)
        staff_user.staff.is_senior = True
        staff_user.staff.save()
        response = self.client.get(reverse('car_rental:staff_detail', kwargs={'pk': 2}))
        self.assertNotContains(response, 'You have no staffs.')
        self.assertContains(response, staff_user.username)
        self.assertContains(response, "Senior")


class StaffDeleteViewTest(TestCase):

    def test_not_staff(self):
        user = login_a_user(self.client)
        response = self.client.get(reverse('car_rental:delete_staff', kwargs={'pk': 1}))
        self.assertEqual(response.status_code, 403)

    def test_access_denied(self):
        user = login_a_user(self.client, is_staff=True)
        response = self.client.get(reverse('car_rental:delete_staff', kwargs={'pk': 1}))
        self.assertEqual(response.status_code, 403)

    def test_no_staffs(self):
        user = login_a_user(self.client, is_staff=True)
        user.staff.add_permissions('can_access_staff')
        response = self.client.get(reverse('car_rental:delete_staff', kwargs={'pk': 2}))
        self.assertEqual(response.status_code, 404)

    def test_normal_staff(self):
        staff_user = login_a_user(self.client, is_staff=True)
        staff_user.staff.add_permissions('can_access_staff')
        staff_user = create_user(is_staff=True, exhibition=staff_user.staff.exhibition)
        response = self.client.post(reverse('car_rental:delete_staff', kwargs={'pk': 2}), {'Yes': True})
        self.assertRedirects(response, reverse('car_rental:staff'))
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(Staff.objects.count(), 1)
        self.assertNotEqual(User.objects.get().username, staff_user.username)


class ChangePermissionsViewTest(TestCase):

    def test_not_have_staff_permission(self):
        user = login_a_user(client=self.client, is_staff=True)
        staff = user.staff
        staff2 = create_user(is_staff=True, exhibition=staff.exhibition)
        data = {'perms': ['can_access_credit']}
        response = self.client.post(reverse('car_rental:staff_perms', kwargs={'pk': staff2.id}))
        self.assertEqual(response.status_code, 403)

    def test_can_access_credit_permission(self):
        user = login_a_user(client=self.client, is_staff=True)
        staff = user.staff
        staff.add_permissions('can_access_staff')
        staff2 = create_user(is_staff=True, exhibition=staff.exhibition).staff
        data = {'perms': ['CREDIT']}
        response = self.client.post(reverse('car_rental:staff_perms', kwargs={'pk': staff2.id}), data)
        self.assertRedirects(response, reverse('car_rental:staff_detail', kwargs={'pk': staff2.id}))
        self.assertTrue(staff2.user.has_perm('car_rental.can_access_credit'))

    def test_can_answer_request_permission(self):
        user = login_a_user(client=self.client, is_staff=True)
        staff = user.staff
        staff.add_permissions('can_access_staff')
        staff2 = create_user(is_staff=True, exhibition=staff.exhibition).staff
        data = {'perms': ['REQUEST']}
        response = self.client.post(reverse('car_rental:staff_perms', kwargs={'pk': staff2.id}), data)
        self.assertRedirects(response, reverse('car_rental:staff_detail', kwargs={'pk': staff2.id}))
        self.assertTrue(staff2.user.has_perm('car_rental.can_answer_request'))

    def test_can_access_car_permission(self):
        user = login_a_user(client=self.client, is_staff=True)
        staff = user.staff
        staff.add_permissions('can_access_staff')
        staff2 = create_user(is_staff=True, exhibition=staff.exhibition).staff
        data = {'perms': ['CAR']}
        response = self.client.post(reverse('car_rental:staff_perms', kwargs={'pk': staff2.id}), data)
        self.assertRedirects(response, reverse('car_rental:staff_detail', kwargs={'pk': staff2.id}))
        self.assertTrue(staff2.user.has_perm('car_rental.can_access_car'))

    def test_can_access_staff_permission(self):
        user = login_a_user(client=self.client, is_staff=True)
        staff = user.staff
        staff.add_permissions('can_access_staff')
        staff2 = create_user(is_staff=True, exhibition=staff.exhibition).staff
        data = {'perms': ['STAFF']}
        response = self.client.post(reverse('car_rental:staff_perms', kwargs={'pk': staff2.id}), data)
        self.assertRedirects(response, reverse('car_rental:staff_detail', kwargs={'pk': staff2.id}))
        self.assertTrue(staff2.user.has_perm('car_rental.can_access_staff'))

