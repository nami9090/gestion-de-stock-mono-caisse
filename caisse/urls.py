from django.urls import path
from . import views

urlpatterns = [
	path('dashboard/', views.home_caisse, name='home_caisse'),
	path('vente-liste-caisse/', views.sale_list_caisse, name='sale_list_caisse'),
	path('vente-creer-caisse/', views.sale_create_caisse, name='sale_create_caisse'),
	path('vente-delete-caisse/<int:pk>/', views.sale_delete_caisse, name='sale_delete_caisse'),
	path('vente-detail-caisse/<int:pk>/', views.sale_detail_caisse, name='sale_detail_caisse'),
	path('vente-update-caisse/<int:pk>/', views.sale_form_caisse, name='sale_form_caisse'),
	path('vente-invoice-caisse/<int:pk>/', views.sale_invoice_caisse, name='sale_invoice_caisse'),
	path('confirmer-suppression-caisse/<int:pk>/', views.saleitem_confirm_delete_caisse, name='saleitem_confirm_delete_caisse'),
	path('vente-finaliser-caisse/', views.sale_finalize_caisse, name='sale_finalize_caisse'),

	path('produits-liste/', views.gestion_produit, name='gestion_produit'),

	path('vente-ticket/<int:pk>/', views.sale_invoice_pos_caisse, name='sale_invoice_pos_caisse'),
	path('generate-invoice/<int:pk>/', views.generate_invoice, name='generate_invoice'),

]