from django.conf import settings
from django.db import models
from django.db.models import Q


class Appointment(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        CONFIRMED = 'confirmed', 'Confirmed'
        REJECTED = 'rejected', 'Rejected'
        CANCELLED = 'cancelled', 'Cancelled'

    # Only these statuses hold on to a slot.
    ACTIVE_STATUSES = (Status.PENDING, Status.CONFIRMED)

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='appointments'
    )
    provider = models.ForeignKey(
        'providers.ProviderProfile', on_delete=models.CASCADE, related_name='appointments'
    )
    service = models.ForeignKey('providers.Service', on_delete=models.PROTECT, related_name='appointments')
    date = models.DateField()
    time = models.TimeField()
    end_time = models.TimeField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-time']
        constraints = [
            # Last line of defence against double booking, even if two requests race.
            models.UniqueConstraint(
                fields=['provider', 'date', 'time'],
                condition=Q(status__in=['pending', 'confirmed']),
                name='no_double_booking',
            ),
        ]

    def __str__(self):
        return f'{self.customer} -> {self.provider} on {self.date} {self.time:%H:%M} [{self.status}]'
