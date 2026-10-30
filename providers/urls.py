from django.urls import path

from . import views

urlpatterns = [
    path('providers/', views.ProviderListView.as_view(), name='provider-list'),
    path('providers/me/', views.MyProviderProfileView.as_view(), name='provider-me'),
    path('providers/<int:pk>/', views.ProviderDetailView.as_view(), name='provider-detail'),

    path('services/', views.ServiceListCreateView.as_view(), name='service-list'),
    path('services/<int:pk>/', views.ServiceDetailView.as_view(), name='service-detail'),

    path('availability/', views.AvailabilityListCreateView.as_view(), name='availability-list'),
    path('availability/slots/', views.AvailableSlotsView.as_view(), name='availability-slots'),
    path('availability/<int:pk>/', views.AvailabilityDetailView.as_view(), name='availability-detail'),
]
