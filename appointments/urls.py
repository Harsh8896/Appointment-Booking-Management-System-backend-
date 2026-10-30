from django.urls import path

from . import views

urlpatterns = [
    path('appointments/', views.AppointmentListCreateView.as_view(), name='appointment-list'),
    path('appointments/<int:pk>/', views.AppointmentDetailView.as_view(), name='appointment-detail'),
    path('appointments/<int:pk>/cancel/', views.CancelAppointmentView.as_view(), name='appointment-cancel'),
    path('appointments/<int:pk>/confirm/', views.ConfirmAppointmentView.as_view(), name='appointment-confirm'),
    path('appointments/<int:pk>/reject/', views.RejectAppointmentView.as_view(), name='appointment-reject'),
]
