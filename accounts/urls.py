from django.urls import path
from . import views

urlpatterns = [
	path('', views.login_view, name='login'),
	path('logout-session/', views.logout_view, name='logout'),
]