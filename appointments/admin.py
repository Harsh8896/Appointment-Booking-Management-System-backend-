from django.contrib import admin

from .models import Appointment


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('customer', 'provider', 'service', 'date', 'time', 'status')
    list_filter = ('status', 'date', 'provider')
    search_fields = ('customer__name', 'provider__user__name')
