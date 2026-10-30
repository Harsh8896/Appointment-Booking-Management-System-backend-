from rest_framework import generics
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from accounts.permissions import IsProvider, IsProviderOrReadOnly
from appointments.services import get_free_slots

from .filters import AvailabilityFilter, ProviderFilter, ServiceFilter
from .models import Availability, ProviderProfile, Service
from .serializers import (
    AvailabilitySerializer,
    ProviderDetailSerializer,
    ProviderListSerializer,
    ProviderProfileUpdateSerializer,
    ServiceSerializer,
    SlotQuerySerializer,
)


class ProviderListView(generics.ListAPIView):
    queryset = ProviderProfile.objects.select_related('user').filter(user__is_active=True).order_by('user__name')
    serializer_class = ProviderListSerializer
    permission_classes = [AllowAny]
    filterset_class = ProviderFilter
    search_fields = ['user__name', 'specialization', 'description', 'services__name']
    ordering_fields = ['experience', 'user__name']

    def filter_queryset(self, queryset):
        # Joins on services/availabilities can repeat the same provider.
        return super().filter_queryset(queryset).distinct()


class ProviderDetailView(generics.RetrieveAPIView):
    queryset = ProviderProfile.objects.select_related('user').prefetch_related('services')
    serializer_class = ProviderDetailSerializer
    permission_classes = [AllowAny]


class MyProviderProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsProvider]
    serializer_class = ProviderProfileUpdateSerializer
    http_method_names = ['get', 'patch', 'head', 'options']

    def get_object(self):
        return self.request.user.provider_profile


class ProviderOwnedMixin:
    """Writes are limited to the logged-in provider's own records."""

    permission_classes = [IsProviderOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(provider=self.request.user.provider_profile)

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.method in ('GET', 'HEAD', 'OPTIONS'):
            return qs
        return qs.filter(provider__user=self.request.user)


class ServiceListCreateView(ProviderOwnedMixin, generics.ListCreateAPIView):
    queryset = Service.objects.select_related('provider__user')
    serializer_class = ServiceSerializer
    filterset_class = ServiceFilter
    search_fields = ['name', 'provider__user__name']
    ordering_fields = ['price', 'duration', 'name']


class ServiceDetailView(ProviderOwnedMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer


class AvailabilityListCreateView(ProviderOwnedMixin, generics.ListCreateAPIView):
    queryset = Availability.objects.all()
    serializer_class = AvailabilitySerializer
    filterset_class = AvailabilityFilter
    ordering_fields = ['date', 'start_time']


class AvailabilityDetailView(ProviderOwnedMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = Availability.objects.all()
    serializer_class = AvailabilitySerializer


class AvailableSlotsView(generics.GenericAPIView):
    """Free slots for a provider's service on a given day: ?provider=1&service=2&date=2026-11-05"""

    permission_classes = [AllowAny]
    serializer_class = SlotQuerySerializer
    pagination_class = None

    def get(self, request):
        params = self.get_serializer(data=request.query_params)
        params.is_valid(raise_exception=True)
        provider = params.validated_data['provider']
        service = params.validated_data['service']
        day = params.validated_data['date']

        slots = get_free_slots(provider, service, day)
        return Response({
            'provider': provider.id,
            'service': service.id,
            'date': day,
            'slots': slots,
        })
