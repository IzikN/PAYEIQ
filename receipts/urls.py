from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing, name='landing'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('update-receipt/', views.update_receipt, name='update_receipt'),
    path('export-excel/', views.export_excel, name='export_excel'),
    path('delete-receipt/', views.delete_receipt, name='delete_receipt'),
]

