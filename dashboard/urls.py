from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('admin/', views.dashboard_admin, name='dashboard_admin'),
    path('caisse/', views.dashboard_caisse, name='dashboard_caisse'),
    path('serveur/', views.dashboard_serveur, name='dashboard_serveur'),
    path('kitchen/',views.dashboard_cuisine,name='dashboard_cuisine'),
]
