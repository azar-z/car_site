import django_filters
from bootstrap_datepicker_plus.widgets import DateTimePickerInput

from car_rental.models import Car, RentRequest


class CarFilterSet(django_filters.FilterSet):
    car_type = django_filters.CharFilter(label='Model', lookup_expr='icontains')
    popular = django_filters.ChoiceFilter(label='', method='popular_cars', choices=[('P', 'popular'), ])

    def popular_cars(self, queryset, name, value):
        queryset2 = Car.objects.none()
        for car in queryset:
            if car.rentrequest_set.count() >= 3:
                queryset2 |= Car.objects.filter(pk=car.pk)
        return queryset2

    class Meta:
        model = Car
        fields = ['car_type']


class RentRequestFilterSet(django_filters.FilterSet):
    rent_start_time = django_filters.DateTimeFilter(widget=DateTimePickerInput(), lookup_expr='gt')

    class Meta:
        model = RentRequest
        fields = ['is_accepted']


class StaffFilterSet(django_filters.FilterSet):
    user__username = django_filters.CharFilter(label='username', lookup_expr='icontains')

    class Meta:
        model = Car
        fields = ['user__username']
