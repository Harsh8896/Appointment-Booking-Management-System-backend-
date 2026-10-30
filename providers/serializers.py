from datetime import date

from rest_framework import serializers

from .models import Availability, ProviderProfile, Service


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ('id', 'provider', 'name', 'duration', 'price')
        read_only_fields = ('provider',)

    def validate_duration(self, value):
        if value < 5:
            raise serializers.ValidationError('Duration must be at least 5 minutes.')
        return value

    def validate_price(self, value):
        if value < 0:
            raise serializers.ValidationError('Price cannot be negative.')
        return value

    def validate_name(self, value):
        provider = self.context['request'].user.provider_profile
        clash = Service.objects.filter(provider=provider, name__iexact=value)
        if self.instance:
            clash = clash.exclude(pk=self.instance.pk)
        if clash.exists():
            raise serializers.ValidationError('You already have a service with this name.')
        return value


class ProviderListSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='user.name', read_only=True)

    class Meta:
        model = ProviderProfile
        fields = ('id', 'name', 'specialization', 'experience')


class ProviderDetailSerializer(ProviderListSerializer):
    services = ServiceSerializer(many=True, read_only=True)

    class Meta(ProviderListSerializer.Meta):
        fields = ProviderListSerializer.Meta.fields + ('description', 'services')


class ProviderProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProviderProfile
        fields = ('id', 'specialization', 'experience', 'description')


class AvailabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Availability
        fields = ('id', 'provider', 'date', 'start_time', 'end_time')
        read_only_fields = ('provider',)

    def validate_date(self, value):
        if value < date.today():
            raise serializers.ValidationError('Cannot add availability for a past date.')
        return value

    def validate(self, attrs):
        # On PATCH some fields may be missing, so fall back to the existing values.
        current = self.instance
        day = attrs.get('date', current.date if current else None)
        start = attrs.get('start_time', current.start_time if current else None)
        end = attrs.get('end_time', current.end_time if current else None)

        if start >= end:
            raise serializers.ValidationError({'end_time': 'End time must be after start time.'})

        provider = self.context['request'].user.provider_profile
        overlapping = Availability.objects.filter(
            provider=provider, date=day, start_time__lt=end, end_time__gt=start
        )
        if current:
            overlapping = overlapping.exclude(pk=current.pk)
        if overlapping.exists():
            raise serializers.ValidationError('This overlaps with another availability you already added.')
        return attrs


class SlotQuerySerializer(serializers.Serializer):
    provider = serializers.PrimaryKeyRelatedField(queryset=ProviderProfile.objects.all())
    service = serializers.PrimaryKeyRelatedField(queryset=Service.objects.all())
    date = serializers.DateField()

    def validate(self, attrs):
        if attrs['service'].provider_id != attrs['provider'].id:
            raise serializers.ValidationError({'service': 'This service does not belong to the provider.'})
        return attrs
