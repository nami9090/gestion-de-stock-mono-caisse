from django.urls import path
from . import views

app_name = 'paiement'

urlpatterns = [
	path('', views.paiement_list, name='paiement_list'),
	path('<int:facture_id>/create/', views.paiement_create, name='paiement_create'),
	path('<int:pk>/update/', views.paiement_update, name='paiement_update'),
	path('<int:pk>/delete/', views.paiement_delete, name='paiement_delete'),
	path('<int:pk>/detail/', views.paiement_detail, name='paiement_detail'),
]