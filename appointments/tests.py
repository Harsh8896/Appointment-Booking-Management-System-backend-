from datetime import date, time, timedelta

from django.urls import reverse
from rest_framework.test import APITestCase

from accounts.models import User
from providers.models import Availability, Service

from .models import Appointment


class BookingFlowTests(APITestCase):
    def setUp(self):
        self.day = date.today() + timedelta(days=3)

        self.provider_user = User.objects.create_user('doc@test.com', 'pass12345', name='Dr. Doc', role='provider')
        from providers.models import ProviderProfile
        self.provider = ProviderProfile.objects.create(user=self.provider_user, specialization='Dentist')
        self.service = Service.objects.create(provider=self.provider, name='Checkup', duration=30, price=500)
        Availability.objects.create(
            provider=self.provider, date=self.day, start_time=time(10, 0), end_time=time(12, 0)
        )

        self.alice = User.objects.create_user('alice@test.com', 'pass12345', name='Alice')
        self.bob = User.objects.create_user('bob@test.com', 'pass12345', name='Bob')

    def book(self, user, at=time(10, 0)):
        self.client.force_authenticate(user)
        return self.client.post(reverse('appointment-list'), {
            'provider': self.provider.id,
            'service': self.service.id,
            'date': self.day.isoformat(),
            'time': at.strftime('%H:%M'),
        })

    def test_slots_exclude_booked_time(self):
        self.book(self.alice, time(10, 0))
        self.client.force_authenticate(None)
        res = self.client.get(reverse('availability-slots'), {
            'provider': self.provider.id, 'service': self.service.id, 'date': self.day.isoformat(),
        })
        starts = [s['start_time'] for s in res.data['slots']]
        self.assertNotIn(time(10, 0), starts)
        self.assertIn(time(10, 30), starts)

    def test_double_booking_is_blocked(self):
        self.assertEqual(self.book(self.alice).status_code, 201)
        self.assertEqual(self.book(self.bob).status_code, 400)

    def test_overlapping_slot_is_blocked(self):
        self.book(self.alice, time(10, 0))
        self.assertEqual(self.book(self.bob, time(10, 15)).status_code, 400)

    def test_cancelled_slot_can_be_rebooked(self):
        appt_id = self.book(self.alice).data['id']
        self.client.force_authenticate(self.alice)
        self.client.post(reverse('appointment-cancel', args=[appt_id]))
        self.assertEqual(self.book(self.bob).status_code, 201)

    def test_outside_availability_is_rejected(self):
        self.assertEqual(self.book(self.alice, time(15, 0)).status_code, 400)

    def test_reschedule_moves_back_to_pending(self):
        appt_id = self.book(self.alice).data['id']
        appt = Appointment.objects.get(pk=appt_id)
        appt.status = Appointment.Status.CONFIRMED
        appt.save()

        res = self.client.patch(reverse('appointment-detail', args=[appt_id]), {'time': '11:00'})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['status'], 'pending')
        self.assertEqual(res.data['time'], '11:00:00')

    def test_provider_confirms_and_customer_cannot(self):
        appt_id = self.book(self.alice).data['id']
        url = reverse('appointment-confirm', args=[appt_id])

        self.assertEqual(self.client.post(url).status_code, 403)

        self.client.force_authenticate(self.provider_user)
        res = self.client.post(url)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['status'], 'confirmed')

    def test_customer_cannot_see_others_appointments(self):
        appt_id = self.book(self.alice).data['id']
        self.client.force_authenticate(self.bob)
        self.assertEqual(self.client.get(reverse('appointment-detail', args=[appt_id])).status_code, 404)

    def test_register_and_login(self):
        self.client.force_authenticate(None)
        res = self.client.post(reverse('register'), {
            'name': 'New', 'email': 'new@test.com', 'password': 'Str0ngPass!9', 'role': 'provider',
        })
        self.assertEqual(res.status_code, 201)
        login = self.client.post(reverse('login'), {'email': 'new@test.com', 'password': 'Str0ngPass!9'})
        self.assertEqual(login.status_code, 200)
        self.assertIn('access', login.data)
