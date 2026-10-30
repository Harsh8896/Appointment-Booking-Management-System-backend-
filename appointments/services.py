from datetime import datetime, timedelta

from django.utils import timezone
from rest_framework import serializers

from providers.models import Availability

from .models import Appointment


def booked_appointments(provider, day, exclude_pk=None):
    """Appointments that still block the provider's calendar."""
    qs = Appointment.objects.filter(provider=provider, date=day, status__in=Appointment.ACTIVE_STATUSES)
    if exclude_pk:
        qs = qs.exclude(pk=exclude_pk)
    return qs


def is_slot_taken(provider, day, start, end, exclude_pk=None):
    return booked_appointments(provider, day, exclude_pk).filter(time__lt=end, end_time__gt=start).exists()


def end_time_for(service, day, start):
    return (datetime.combine(day, start) + timedelta(minutes=service.duration)).time()


def validate_booking(provider, service, day, start, exclude_pk=None):
    """Raises ValidationError if the slot can't be booked, otherwise returns the end time."""
    if service.provider_id != provider.id:
        raise serializers.ValidationError({'service': 'This service does not belong to the selected provider.'})

    now = timezone.localtime()
    if datetime.combine(day, start) <= now.replace(tzinfo=None):
        raise serializers.ValidationError('You cannot book a slot in the past.')

    end = end_time_for(service, day, start)
    if end <= start:
        raise serializers.ValidationError('The appointment must finish on the same day.')

    fits_in_window = Availability.objects.filter(
        provider=provider, date=day, start_time__lte=start, end_time__gte=end
    ).exists()
    if not fits_in_window:
        raise serializers.ValidationError('The provider is not available at this time.')

    if is_slot_taken(provider, day, start, end, exclude_pk):
        raise serializers.ValidationError('This slot is already booked. Please choose another time.')

    return end


def get_free_slots(provider, service, day):
    """Split each availability window into service-length slots and drop the booked ones."""
    step = timedelta(minutes=service.duration)
    booked = list(booked_appointments(provider, day).values_list('time', 'end_time'))
    now = timezone.localtime().replace(tzinfo=None)

    slots = []
    for window in Availability.objects.filter(provider=provider, date=day):
        current = datetime.combine(day, window.start_time)
        window_end = datetime.combine(day, window.end_time)
        while current + step <= window_end:
            start, end = current.time(), (current + step).time()
            clashes = any(start < b_end and end > b_start for b_start, b_end in booked)
            if not clashes and current > now:
                slots.append({'start_time': start, 'end_time': end})
            current += step
    return slots
