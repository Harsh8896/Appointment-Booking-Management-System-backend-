from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.models import User
from accounts.permissions import IsCustomer

from .filters import AppointmentFilter
from .models import Appointment
from .serializers import AppointmentSerializer, RescheduleSerializer


class AppointmentQuerysetMixin:
    """Each role only sees the appointments that concern them."""

    def get_queryset(self):
        user = self.request.user
        qs = Appointment.objects.select_related('customer', 'provider__user', 'service')
        if user.role == User.Role.ADMIN:
            return qs
        if user.role == User.Role.PROVIDER:
            return qs.filter(provider__user=user)
        return qs.filter(customer=user)


class AppointmentListCreateView(AppointmentQuerysetMixin, generics.ListCreateAPIView):
    serializer_class = AppointmentSerializer
    filterset_class = AppointmentFilter
    search_fields = ['provider__user__name', 'customer__name', 'service__name']
    ordering_fields = ['date', 'time', 'created_at']

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsCustomer()]
        return [IsAuthenticated()]


class AppointmentDetailView(AppointmentQuerysetMixin, generics.RetrieveUpdateAPIView):
    """GET to view, PATCH to reschedule (customer only)."""

    http_method_names = ['get', 'patch', 'head', 'options']

    def get_serializer_class(self):
        if self.request.method == 'PATCH':
            return RescheduleSerializer
        return AppointmentSerializer

    def get_permissions(self):
        if self.request.method == 'PATCH':
            return [IsCustomer()]
        return [IsAuthenticated()]

    def update(self, request, *args, **kwargs):
        super().update(request, *args, **kwargs)
        return Response(AppointmentSerializer(self.get_object(), context=self.get_serializer_context()).data)


class AppointmentStatusView(AppointmentQuerysetMixin, generics.GenericAPIView):
    """Base for the one-click actions: cancel, confirm and reject."""

    serializer_class = AppointmentSerializer
    new_status = None
    allowed_from = ()
    allowed_roles = ()

    def post(self, request, pk):
        appointment = self.get_object()

        if request.user.role not in self.allowed_roles:
            raise PermissionDenied('You are not allowed to do this.')
        if appointment.status not in self.allowed_from:
            return Response(
                {'detail': f'A {appointment.status} appointment cannot be changed to {self.new_status}.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        appointment.status = self.new_status
        appointment.save(update_fields=['status', 'updated_at'])
        return Response(self.get_serializer(appointment).data)


class CancelAppointmentView(AppointmentStatusView):
    new_status = Appointment.Status.CANCELLED
    allowed_from = Appointment.ACTIVE_STATUSES
    allowed_roles = (User.Role.CUSTOMER, User.Role.PROVIDER, User.Role.ADMIN)


class ConfirmAppointmentView(AppointmentStatusView):
    new_status = Appointment.Status.CONFIRMED
    allowed_from = (Appointment.Status.PENDING,)
    allowed_roles = (User.Role.PROVIDER, User.Role.ADMIN)


class RejectAppointmentView(AppointmentStatusView):
    new_status = Appointment.Status.REJECTED
    allowed_from = (Appointment.Status.PENDING,)
    allowed_roles = (User.Role.PROVIDER, User.Role.ADMIN)
