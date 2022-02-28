import django_tables2 as tables
from django.urls import reverse
from django.utils.html import format_html

from car_rental.models import Car, RentRequest, Staff


class CarStaffTable(tables.Table):
    car_type = tables.Column()
    rent_end_time = tables.Column(verbose_name='Status')

    def render_car_type(self, value, record):
        return format_html("<a href=\"{0}\">{1}</a>", reverse('car_rental:car', kwargs={'pk': record.id}), value)

    def render_rent_end_time(self, value, record):
        status = 'free' if not record.is_rented() else 'rented'
        color = 'darkgreen' if not record.is_rented() else 'darkred'
        return format_html("<span style=\"color: " + color + "\">" + status + "</span>")

    class Meta:
        model = Car
        fields = ['car_type', 'plate']
        template_name = 'django_tables2/bootstrap-responsive.html'


class RentRequestRenterTable(tables.Table):
    has_result = tables.Column(verbose_name='Status')
    car__owner__name = tables.Column(verbose_name='Exhibition')

    def render_car__car_type(self, value, record):
        return format_html("<a href=\"{0}\">{1}</a>", reverse('car_rental:car', kwargs={'pk': record.car.id}), value)

    def render_has_result(self, value, record):
        status = 'Not determined yet'
        color = 'black'
        if value:
            status = 'Accepted' if record.is_accepted else 'Rejected'
            color = 'darkgreen' if record.is_accepted else 'darkred'
        return format_html("<span style=\"color: " + color + "\">" + status + "</span>")

    class Meta:
        model = RentRequest
        fields = ['car__car_type', 'rent_start_time', 'rent_end_time', 'car__owner__name']
        template_name = 'django_tables2/bootstrap-responsive.html'


class StaffTable(tables.Table):
    is_senior = tables.Column(verbose_name='Type')

    def render_is_senior(self, value, record):
        status = 'Senior' if record.is_senior else 'Normal'
        color = 'darkgreen' if record.is_senior else 'black'
        return format_html("<span style=\"color: " + color + "\">" + status + "</span>")

    def render_user__username(self, value, record):
        return format_html("<a href=\"{0}\">{1}</a>", reverse('car_rental:staff_detail', kwargs={'pk': record.id}), value)

    class Meta:
        model = Staff
        fields = ['user__username', 'is_senior']
        template_name = 'django_tables2/bootstrap-responsive.html'
