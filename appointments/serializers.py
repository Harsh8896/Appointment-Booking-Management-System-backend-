from django.db import IntegrityError, transaction
from rest_framework import serializers

from .models import Appointment
from .services import end_time_for, is_slot_taken, validate_booking


class AppointmentSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    provider_name = serializers.CharField(source='provider.user.name', read_only=True)
    service_name = serializers.CharField(source='service.name', read_only=True)

    class Meta:
        model = Appointment
        fields = (
            'id', 'customer', 'customer_name', 'provider', 'provider_name',
            'service', 'service_name', 'date', 'time', 'end_time', 'status', 'created_at',
        )
        read_only_fields = ('customer', 'end_time', 'status', 'created_at')

    def validate(self, attrs):
        attrs['end_time'] = validate_booking(attrs['provider'], attrs['service'], attrs['date'], attrs['time'])
        return attrs

    def create(self, validated_data):
        validated_data['customer'] = self.context['request'].user
        try:
            with transaction.atomic():
                # Re-check inside the transaction in case someone booked it a moment ago.
                if is_slot_taken(
                    validated_data['provider'], validated_data['date'],
                    validated_data['time'], validated_data['end_time'],
                ):
                    raise serializers.ValidationError('This slot is already booked. Please choose another time.')
                return super().create(validated_data)
        except IntegrityError:
            raise serializers.ValidationError('This slot is already booked. Please choose another time.')


class RescheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = ('date', 'time')

    def validate(self, attrs):
        appt = self.instance
        if appt.status not in Appointment.ACTIVE_STATUSES:
            raise serializers.ValidationError(f'A {appt.status} appointment cannot be rescheduled.')

        day = attrs.get('date', appt.date)
        start = attrs.get('time', appt.time)
        # Exclude the appointment itself so it doesn't clash with its own old slot.
        validate_booking(appt.provider, appt.service, day, start, exclude_pk=appt.pk)
        return attrs

    def update(self, instance, validated_data):
        instance.date = validated_data.get('date', instance.date)
        instance.time = validated_data.get('time', instance.time)
        instance.end_time = end_time_for(instance.service, instance.date, instance.time)
        # A moved appointment needs the provider's approval again.
        instance.status = Appointment.Status.PENDING
        try:
            with transaction.atomic():
                instance.save()
        except IntegrityError:
            raise serializers.ValidationError('This slot is already booked. Please choose another time.')
        return instance
