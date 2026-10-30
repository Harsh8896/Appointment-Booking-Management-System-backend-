from datetime import time, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import User
from appointments.models import Appointment
from appointments.services import validate_booking
from providers.models import Availability, ProviderProfile, Service

PASSWORD = 'Test@12345'

PROVIDERS = [
    ('Dr. Aarav Sharma', 'aarav@example.com', 'Dentist', 10, [('Dental Checkup', 30, 500), ('Teeth Cleaning', 45, 1200)]),
    ('Dr. Meera Iyer', 'meera@example.com', 'Dermatologist', 8, [('Skin Consultation', 30, 800), ('Acne Treatment', 40, 1500)]),
    ('Rohan Mehta', 'rohan@example.com', 'Career Consultant', 6, [('Career Counselling', 60, 1000)]),
    ('Dr. Priya Nair', 'priya@example.com', 'Physiotherapist', 12, [('Physio Session', 45, 900), ('Back Pain Therapy', 60, 1400)]),
    ('Kabir Singh', 'kabir@example.com', 'Legal Consultant', 15, [('Legal Advice', 30, 2000)]),
]

CUSTOMERS = [
    ('Ananya Gupta', 'ananya@example.com'),
    ('Vikram Rao', 'vikram@example.com'),
    ('Sneha Patil', 'sneha@example.com'),
    ('Arjun Verma', 'arjun@example.com'),
    ('Isha Kapoor', 'isha@example.com'),
]


class Command(BaseCommand):
    help = 'Creates sample providers, customers, availability and appointments for trying out the API.'

    def handle(self, *args, **options):
        today = timezone.localdate()
        profiles = []

        for name, email, spec, years, services in PROVIDERS:
            user, _ = User.objects.get_or_create(
                email=email, defaults={'name': name, 'role': User.Role.PROVIDER}
            )
            if not user.has_usable_password():
                user.set_password(PASSWORD)
                user.save()
            profile, _ = ProviderProfile.objects.get_or_create(
                user=user,
                defaults={'specialization': spec, 'experience': years, 'description': f'{spec} with {years} years of experience.'},
            )
            for svc_name, duration, price in services:
                Service.objects.get_or_create(
                    provider=profile, name=svc_name, defaults={'duration': duration, 'price': price}
                )
            for offset in range(1, 6):
                Availability.objects.get_or_create(
                    provider=profile, date=today + timedelta(days=offset),
                    defaults={'start_time': time(10, 0), 'end_time': time(17, 0)},
                )
            profiles.append(profile)

        customers = []
        for name, email in CUSTOMERS:
            user, created = User.objects.get_or_create(email=email, defaults={'name': name})
            if created:
                user.set_password(PASSWORD)
                user.save()
            customers.append(user)

        statuses = [
            Appointment.Status.PENDING, Appointment.Status.CONFIRMED, Appointment.Status.PENDING,
            Appointment.Status.CANCELLED, Appointment.Status.REJECTED,
        ]
        for i, (customer, profile, status) in enumerate(zip(customers, profiles, statuses)):
            if Appointment.objects.filter(customer=customer, provider=profile).exists():
                continue
            service = profile.services.first()
            day, start = today + timedelta(days=i % 3 + 1), time(10 + i, 0)
            end = validate_booking(profile, service, day, start)
            Appointment.objects.create(
                customer=customer, provider=profile, service=service,
                date=day, time=start, end_time=end, status=status,
            )

        self.stdout.write(self.style.SUCCESS(
            f'Done. Providers: {len(PROVIDERS)}, customers: {len(CUSTOMERS)}, '
            f'appointments: {Appointment.objects.count()}. Password for all: {PASSWORD}'
        ))
