from django.contrib import admin

from .models import Availability, ProviderProfile, Service


@admin.register(ProviderProfile)
class ProviderProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'specialization', 'experience')
    search_fields = ('user__name', 'specialization')


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'provider', 'duration', 'price')
    list_filter = ('provider',)


@admin.register(Availability)
class AvailabilityAdmin(admin.ModelAdmin):
    list_display = ('provider', 'date', 'start_time', 'end_time')
    list_filter = ('provider', 'date')
