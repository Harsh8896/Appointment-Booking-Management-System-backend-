import django_filters

from .models import Availability, ProviderProfile, Service


class ProviderFilter(django_filters.FilterSet):
    service = django_filters.CharFilter(field_name='services__name', lookup_expr='icontains')
    date = django_filters.DateFilter(field_name='availabilities__date')
    specialization = django_filters.CharFilter(lookup_expr='icontains')
    min_experience = django_filters.NumberFilter(field_name='experience', lookup_expr='gte')

    class Meta:
        model = ProviderProfile
        fields = []


class ServiceFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains')
    max_price = django_filters.NumberFilter(field_name='price', lookup_expr='lte')

    class Meta:
        model = Service
        fields = ['provider']


class AvailabilityFilter(django_filters.FilterSet):
    date_from = django_filters.DateFilter(field_name='date', lookup_expr='gte')
    date_to = django_filters.DateFilter(field_name='date', lookup_expr='lte')

    class Meta:
        model = Availability
        fields = ['provider', 'date']
