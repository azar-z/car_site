import django_filters
from bootstrap_datepicker_plus.widgets import DateTimePickerInput

from car_rental.models import Car, RentRequest


class CarFilterSet(django_filters.FilterSet):
    car_type = django_filters.CharFilter(label='Model', lookup_expr='icontains')

    class Meta:
        model = Car
        fields = ['id']


class RentRequestFilterSet(django_filters.FilterSet):
    rent_start_time = django_filters.DateTimeFilter(widget=DateTimePickerInput(), lookup_expr='gt')

    class Meta:
        model = RentRequest
        fields = ['requester', 'has_result', 'is_accepted']


class StaffFilterSet(django_filters.FilterSet):
    user__username = django_filters.CharFilter(label='username', lookup_expr='icontains')

    class Meta:
        model = Car
        fields = ['id']
