from django.urls import path
from . import views

urlpatterns = [
	path('settings/', views.shop_settings_view, name='shop_settings_view'),

	#Suppliers

	path('fournisseur-liste/', views.supplier_list, name='supplier_list'),
	path('ajouter-fournisseur/', views.supplier_create, name='supplier_create'),
	path('update-fournisseur/<int:pk>/', views.supplier_update, name='supplier_update'),
	path('effacer-fournisseur/<int:pk>/', views.supplier_delete, name='supplier_delete'),

]