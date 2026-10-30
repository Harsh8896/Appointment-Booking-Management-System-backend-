from django.conf import settings
from django.db import models


class ProviderProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='provider_profile'
    )
    specialization = models.CharField(max_length=150, blank=True)
    experience = models.PositiveSmallIntegerField(default=0, help_text='Years of experience')
    description = models.TextField(blank=True)

    def __str__(self):
        return self.user.name


class Service(models.Model):
    provider = models.ForeignKey(ProviderProfile, on_delete=models.CASCADE, related_name='services')
    name = models.CharField(max_length=150)
    duration = models.PositiveSmallIntegerField(help_text='Duration in minutes')
    price = models.DecimalField(max_digits=8, decimal_places=2)

    class Meta:
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(fields=['provider', 'name'], name='unique_service_per_provider'),
        ]

    def __str__(self):
        return f'{self.name} ({self.duration} min)'


class Availability(models.Model):
    provider = models.ForeignKey(ProviderProfile, on_delete=models.CASCADE, related_name='availabilities')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        ordering = ['date', 'start_time']
        verbose_name_plural = 'availabilities'

    def __str__(self):
        return f'{self.provider} - {self.date} {self.start_time:%H:%M}-{self.end_time:%H:%M}'
