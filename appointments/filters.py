import django_filters

from .models import Appointment


class AppointmentFilter(django_filters.FilterSet):
    date_from = django_filters.DateFilter(field_name='date', lookup_expr='gte')
    date_to = django_filters.DateFilter(field_name='date', lookup_expr='lte')

    class Meta:
        model = Appointment
        fields = ['status', 'provider', 'service', 'date']
