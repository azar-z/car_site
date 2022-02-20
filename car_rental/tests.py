import datetime

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from car_rental.models import User, Car, RentRequest


def create_user(username='Farhad', password='1111'):
    user = User.objects.create_user(username=username, password=password)
    user.save()
    return user


class LoginViewTest(TestCase):
    def test_login_existing_activated_renter(self):
        username = 'Farhad'
        password = '1111'
        create_user(username, password)
        response = self.client.post(reverse('car_rental:login'),
                                    {'username': username, 'password': password})
        self.assertRedirects(response, reverse('car_rental:home'))

    def test_login_existing_activated_exhibition(self):
        username = 'Farhad'
        password = '1111'
        user = create_user(username, password)
        user.isCarExhibition = True
        user.save()
        response = self.client.post(reverse('car_rental:login'),
                                    {'username': username, 'password': password})
        self.assertRedirects(response, reverse('car_rental:home'))

    def test_login_existing_not_activated_user(self):
        username = 'Farhad'
        password = '1111'
        data = {'username': username, 'password': password}
        user = create_user(username, password)
        user.is_active = False
        user.save()
        response = self.client.post(reverse('car_rental:login'), data)
        self.assertFormError(response, 'form', None, "Username and Password didn't match.")

    def test_login_not_existing_user(self):
        username = 'Farhad'
        password = '1111'
        data = {'username': username, 'password': password}
        response = self.client.post(reverse('car_rental:login'), data)
        self.assertFormError(response, 'form', None, "Username and Password didn't match.")


def login_a_user(client):
    user = create_user()
    client.force_login(user)
    return user


def create_car(car_type='type1'):
    car = Car.objects.create(car_type=car_type)
    car.save()
    return car


def create_rented_car(renter=None, owner=None, days=1):
    if not renter:
        renter = create_user('renter1')
    if not owner:
        owner = create_user('owner1')
    car = create_car()
    car.rent_end_time = timezone.now() + datetime.timedelta(days=days)
    car.renter = renter
    car.owner = owner
    car.save()
    return car


class CarListViewTest(TestCase):

    def test_not_login(self):
        response = self.client.post(reverse('car_rental:cars'))
        self.assertRedirects(response, "/rental/?next=" + reverse('car_rental:cars'))

    def test_no_car_exists(self):
        login_a_user(self.client)
        response = self.client.get(reverse('car_rental:cars'))
        self.assertContains(response, 'Available Cars')
        self.assertContains(response, "There are no available cars for you!")

    def test_no_car_exists_owner(self):
        owner = login_a_user(self.client)
        owner.isCarExhibition = True
        owner.save()
        car = create_car()
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

    # this test gets wrong once in a while
    def test_show_not_rented_car_to_owner(self):
        owner = login_a_user(self.client)
        owner.isCarExhibition = True
        owner.save()
        car = create_car()
        car.owner = owner
        car.save()
        response = self.client.get(reverse('car_rental:cars'))
        self.assertContains(response, 'Your Cars')
        self.assertNotContains(response, "You have no cars!")
        self.assertContains(response, car.car_type)
        self.assertContains(response, car.id)
        self.assertContains(response, 'free')
        self.assertContains(response, 'Status')

    def test_show_rented_car_to_owner(self):
        owner = login_a_user(self.client)
        owner.isCarExhibition = True
        owner.save()
        car = create_rented_car(renter=create_user('renter'), owner=owner)
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
        create_car()
        response = self.client.get(reverse('car_rental:car', kwargs={'pk': 1}))
        self.assertRedirects(response, "/rental/?next=" + str(reverse('car_rental:car', kwargs={'pk': 1})))

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
        self.assertContains(response, car.owner.username)

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
        car = create_rented_car(renter)
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
        self.assertContains(response, car.owner.username)


    def test_rented_car_by_owner(self):
        owner = login_a_user(self.client)
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
        response = self.client.get(reverse('car_rental:car', kwargs={'pk': 1}))
        self.assertRedirects(response, "/rental/?next=" + str(reverse('car_rental:car', kwargs={'pk': 1})))

    def test_exhibition_no_request(self):
        user = login_a_user(self.client)
        user.isCarExhibition = True
        user.save()
        car = create_car()
        car.set_owner(user)
        response = self.client.get(reverse('car_rental:requests'))
        self.assertContains(response, "No Requests")
        self.assertNotContains(response, "Please accept or reject these requests:")

    def test_exhibition_with_unanswered_result(self):
        owner = login_a_user(self.client)
        owner.isCarExhibition = True
        owner.save()
        car = create_car()
        car.set_owner(owner)
        requester = create_user('user1')
        create_request(requester, car)
        response = self.client.get(reverse('car_rental:requests'))
        self.assertNotContains(response, "No Requests")
        self.assertContains(response, "Please accept or reject these requests:")
        self.assertContains(response, car.car_type)
        self.assertContains(response, car.plate)
        self.assertContains(response, requester.username)

    def test_exhibition_with_answered_result(self):
        owner = login_a_user(self.client)
        owner.isCarExhibition = True
        owner.save()
        car = create_car()
        car.set_owner(owner)
        requester = create_user('user1')
        rent_request = create_request(requester, car)
        rent_request.has_result = True
        rent_request.save()
        response = self.client.get(reverse('car_rental:requests'))
        self.assertContains(response, "No Requests")
        self.assertNotContains(response, "Please accept or reject these requests:")
        self.assertNotContains(response, car.car_type)

    def test_renter_with_no_result(self):
        user = login_a_user(self.client)
        car = create_car()
        car.set_owner(user)
        response = self.client.get(reverse('car_rental:requests'))
        self.assertContains(response, "No Requests")
        self.assertNotContains(response, "Please accept or reject these requests:")

    def test_renter_with_unanswered_result(self):
        owner = create_user('user1')
        owner.isCarExhibition = True
        owner.save()
        car = create_car()
        car.set_owner(owner)
        requester = login_a_user(self.client)
        create_request(requester, car)
        response = self.client.get(reverse('car_rental:requests'))
        self.assertNotContains(response, "No Requests")
        self.assertNotContains(response, "Please accept or reject these requests:")
        self.assertContains(response, car.car_type)
        self.assertContains(response, owner.username)
        self.assertContains(response, "Not determined yet")

    def test_renter_with_accepted_result(self):
        owner = create_user('user1')
        owner.isCarExhibition = True
        owner.save()
        car = create_car()
        car.set_owner(owner)
        requester = login_a_user(self.client)
        rent_request = create_request(requester, car)
        rent_request.has_result = True
        rent_request.is_accepted = True
        rent_request.save()
        response = self.client.get(reverse('car_rental:requests'))
        self.assertNotContains(response, "No Requests")
        self.assertNotContains(response, "Please accept or reject these requests:")
        self.assertContains(response, car.car_type)
        self.assertContains(response, owner.username)
        self.assertContains(response, "Accepted")

    def test_renter_with_rejected_result(self):
        owner = create_user('user1')
        owner.isCarExhibition = True
        owner.save()
        car = create_car()
        car.set_owner(owner)
        requester = login_a_user(self.client)
        rent_request = create_request(requester, car)
        rent_request.has_result = True
        rent_request.is_accepted = False
        rent_request.save()
        response = self.client.get(reverse('car_rental:requests'))
        self.assertNotContains(response, "No Requests")
        self.assertNotContains(response, "Please accept or reject these requests:")
        self.assertContains(response, car.car_type)
        self.assertContains(response, owner.username)
        self.assertContains(response, "Rejected")


class AnswerRequestView(TestCase):

    def test_not_login(self):
        response = self.client.post(reverse('car_rental:cars'))
        self.assertRedirects(response, "/rental/?next=" + reverse('car_rental:cars'))

    def test_not_exhibition_user(self):
        user = login_a_user(self.client)
        user.isCarExhibition = False
        user.save()
        response = self.client.get(reverse('car_rental:answer_requests'))
        self.assertRedirects(response, reverse('car_rental:requests'))

    def test_not_answered_request(self):
        owner = login_a_user(self.client)
        owner.isCarExhibition = True
        owner.save()
        car = create_car()
        car.set_owner(owner)
        requester = create_user('user1')
        rent_request = create_request(requester, car)
        response = self.client.get(reverse('car_rental:answer_requests'))
        self.assertRedirects(response, reverse('car_rental:requests'))
        self.assertFalse(rent_request.has_result)
        self.assertEqual(owner.credit, 0)
        self.assertEqual(requester.credit, 0)

    def test_rejected_request(self):
        owner = login_a_user(self.client)
        owner.isCarExhibition = True
        owner.save()
        car = create_car()
        car.set_owner(owner)
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
        owner = login_a_user(self.client)
        owner.isCarExhibition = True
        owner.save()
        car = create_car()
        car.set_owner(owner)
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
        self.assertRedirects(response, "/rental/?next=" + reverse('car_rental:profile'))

    def test_exhibition(self):
        exhibition = login_a_user(self.client)
        exhibition.isCarExhibition = True
        exhibition.save()
        response = self.client.get(reverse('car_rental:profile'))
        self.assertContains(response, exhibition.username)
        self.assertContains(response, 'Exhibition')
        self.assertContains(response, 'Change Password')
        self.assertContains(response, 'Change Credit')


    def test_renter(self):
        renter = login_a_user(self.client)
        response = self.client.get(reverse('car_rental:profile'))
        self.assertContains(response, renter.username)
        self.assertContains(response, 'Renter')
        self.assertContains(response, 'Change Password')
        self.assertContains(response, 'Change Credit')

"""
class PasswordChangeViewTest(TestCase):

    def test_invalid_password(self):
        user = login_a_user(self.client)
        user.set_password('1111')
        user.save()
        response = self.client.post(reverse('car_rental:change_password'),
                                    {'old_password': '1111', 'new_password1': '1234', 'new_password2': '1234'},
                                    follow=True)
        self.assertRedirects(response, '/rental/login/?next=' + reverse('car_rental:change_password'))
        self.assertContains(response, 'This password is too short.')

    def test_wrong_old_password(self):
        user = login_a_user(self.client)
        user.set_password('1111')
        user.save()
        response = self.client.post(reverse('car_rental:change_password'),
                                    data={'old_password': '2222', 'new_password1': '1234qsvg00', 'new_password2': '1234qsvg00'},
                                    follow=True)
        self.assertRedirects(response, '/rental/login/?next=' + reverse('car_rental:change_password'))
        self.assertContains(response, 'correct')

    def test_valid_password_wrong_confirmation(self):
        user = login_a_user(self.client)
        user.set_password('1111')
        user.save()
        response = self.client.post(reverse('car_rental:change_password'),
                                    {'old_password': '1111', 'new_password1': '1234qsvg00',
                                     'new_password2': '1234qsvg'}, follow=True)
        self.assertRedirects(response, '/rental/login/?next=' + reverse('car_rental:change_password'))
        self.assertContains(response, 'The two password fields didn’t match.', html=True)

    def test_successful_password_change(self):
        user = login_a_user(self.client)
        self.assertTrue(user.check_password('1111'))
        response = self.client.post(reverse('car_rental:change_password'),
                                    {'old_password': '1111', 'new_password1': '1234qsvg00',
                                     'new_password2': '1234qsvg00'}, follow=True)
        user.refresh_from_db()
        self.assertTrue(user.check_password('1234qsvg00'))
        self.assertRedirects(response, reverse('car_rental:profile'))
"""


class CreditChangeViewTest(TestCase):

    def test_changes_correctly(self):
        user = login_a_user(self.client)
        self.assertEqual(user.credit, 0)
        response = self.client.post(reverse('car_rental:change_credit'), {'delta_credit': 100}, follow=True)
        user.refresh_from_db()
        self.assertTrue(user.credit, 100)
        self.assertRedirects(response, reverse('car_rental:profile'))


class LogoutViewTest(TestCase):

    def test_logout_successfully(self):
        login_a_user(self.client)
        response = self.client.get(reverse('car_rental:logout'), follow=True)
        self.assertTrue(response.wsgi_request.user.is_anonymous)
        self.assertRedirects(response, reverse('car_rental:home'))


class AddCarViewTest(TestCase):

    def test_successful_car_add(self):
        owner = login_a_user(self.client)
        owner.isCarExhibition = True
        owner.save()
        response = self.client.post(reverse('car_rental:add_car'),
                                    {'car_type': 'type1', 'plate': '1234', 'price_per_hour': '100'},
                                    follow=True)
        owner.refresh_from_db()
        self.assertRedirects(response, reverse('car_rental:car', kwargs={'pk': '1'}))
        self.assertEqual(owner.cars_owned.get(id=1).car_type, 'type1')

    def test_non_exhibition(self):
        login_a_user(self.client)
        response = self.client.post(reverse('car_rental:add_car'),
                                    {'car_type': 'type1', 'plate': '1234', 'price_per_hour': '100'},
                                    follow=True)
        self.assertEqual(response.status_code, 403)


class EditCarTest(TestCase):

    def test_edit_price_successfully(self):
        owner = login_a_user(self.client)
        owner.isCarExhibition = True
        owner.save()
        car = create_car()
        car.owner = owner
        car.price_per_hour = 10
        car.save()
        response = self.client.post(reverse('car_rental:edit_car', kwargs={'pk': '1'}), {'price_per_hour': 100})
        car.refresh_from_db()
        self.assertEqual(car.price_per_hour, 100)
        self.assertRedirects(response, reverse('car_rental:car', kwargs={'pk': '1'}))

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
        non_owner = login_a_user(self.client)
        non_owner.isCarExhibition = True
        non_owner.save()
        owner = create_user('owner2')
        owner.isCarExhibition = True
        owner.save()
        car = create_car()
        car.price_per_hour = 10
        car.owner = owner
        car.save()
        response = self.client.post(reverse('car_rental:edit_car', kwargs={'pk': '1'}), {'price_per_hour': 100})
        car.refresh_from_db()
        self.assertEqual(car.price_per_hour, 10)
        self.assertEqual(response.status_code, 403)

    def test_rented_car(self):
        owner = login_a_user(self.client)
        owner.isCarExhibition = True
        owner.save()
        car = create_rented_car(owner=owner)
        car.owner = owner
        car.price_per_hour = 10
        car.save()
        response = self.client.post(reverse('car_rental:edit_car', kwargs={'pk': '1'}), {'price_per_hour': 100})
        car.refresh_from_db()
        self.assertEqual(car.price_per_hour, 10)
        self.assertEqual(response.status_code, 403)


class NeedRepairViewTest(TestCase):

    def test_non_exhibition(self):
        login_a_user(self.client)
        car = create_car()
        car.needs_repair = False
        car.save()
        response = self.client.post(reverse('car_rental:needs_repair', kwargs={'pk': '1'}), {'needs_repair': True})
        car.refresh_from_db()
        self.assertEqual(response.status_code, 403)
        self.assertFalse(car.needs_repair)

    def test_non_owner_exhibition(self):
        non_owner = login_a_user(self.client)
        non_owner.isCarExhibition = True
        non_owner.save()
        owner = create_user('owner2')
        owner.isCarExhibition = True
        owner.save()
        car = create_car()
        car.needs_repair = False
        car.save()
        response = self.client.post(reverse('car_rental:needs_repair', kwargs={'pk': '1'}), {'needs_repair': True})
        car.refresh_from_db()
        self.assertEqual(response.status_code, 403)
        self.assertFalse(car.needs_repair)

    def test_successful_owner_need_repair(self):
        owner = login_a_user(self.client)
        owner.isCarExhibition = True
        owner.save()
        car = create_car()
        car.needs_repair = False
        car.owner = owner
        car.save()
        response = self.client.post(reverse('car_rental:needs_repair', kwargs={'pk': '1'}), {'needs_repair': True})
        car.refresh_from_db()
        owner.refresh_from_db()
        self.assertTrue(car.needs_repair)
        self.assertEqual(owner.credit, 0)

    def test_successful_renter_need_repair(self):
        owner = create_user('owner1')
        owner.isCarExhibition = True
        owner.save()
        renter = login_a_user(self.client)
        car = create_car()
        car.needs_repair = True
        car.owner = owner
        car.renter = renter
        car.save()
        response = self.client.post(reverse('car_rental:needs_repair', kwargs={'pk': '1'}), {'needs_repair': True})
        car.refresh_from_db()
        renter.refresh_from_db()
        owner.refresh_from_db()
        self.assertFalse(car.needs_repair)
        self.assertEqual(owner.credit, 100)
        self.assertEqual(renter.credit, -100)

    def test_owner_not_need_repair_renter_need_repair(self):
        owner = create_user('owner1')
        owner.isCarExhibition = True
        owner.save()
        renter = login_a_user(self.client)
        car = create_car()
        car.needs_repair = False
        car.owner = owner
        car.renter = renter
        car.save()
        response = self.client.post(reverse('car_rental:needs_repair', kwargs={'pk': '1'}), {'needs_repair': True})
        car.refresh_from_db()
        renter.refresh_from_db()
        owner.refresh_from_db()
        self.assertEqual(response.status_code, 403)
        self.assertFalse(car.needs_repair)
        self.assertEqual(owner.credit, 0)
        self.assertEqual(renter.credit, 0)

    def test_owner_need_repair_renter_not_need_repair(self):
        owner = create_user('owner1')
        owner.isCarExhibition = True
        owner.save()
        renter = login_a_user(self.client)
        car = create_car()
        car.needs_repair = True
        car.owner = owner
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

