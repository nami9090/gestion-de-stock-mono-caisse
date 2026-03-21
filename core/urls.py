from django.urls import path
from . import views

urlpatterns = [
	path('dasboard/', views.home, name='home'),
	path('settings/', views.shop_settings_view, name='shop_settings_view'),
	path('produits-liste/', views.product_list, name='product_list'),
	path('ajouter-produit/', views.product_create, name='product_create'),
	path('update-produit/<int:pk>/', views.product_update, name='product_update'),
	path('effacer-produit/<int:pk>/', views.product_delete, name='product_delete'),
	path('detail-produit/<int:pk>/', views.product_detail, name='product_detail'),
	## categories

	path('categories-liste/', views.category_list, name='category_list'),
	path('ajouter-categorie/', views.category_create, name='category_create'),
	path('update-categorie/<int:pk>/', views.category_update, name='category_update'),
	path('effacer-categorie/<int:pk>/', views.category_delete, name='category_delete'),

	#Suppliers

	path('fournisseur-liste/', views.supplier_list, name='supplier_list'),
	path('ajouter-fournisseur/', views.supplier_create, name='supplier_create'),
	path('update-fournisseur/<int:pk>/', views.supplier_update, name='supplier_update'),
	path('effacer-fournisseur/<int:pk>/', views.supplier_delete, name='supplier_delete'),

	#Stocks
	path('stock-liste/', views.stock_list, name='stock_list'),
	path('ajouter-stock/', views.stock_create, name='stock_create'),

	#Sales
	path('vente-liste/', views.sale_list, name='sale_list'),
	path('creer-vente/', views.sale_create, name='sale_create'),
	path('finaliser-vente/', views.sale_finalize, name='sale_finalize'),
	path('update-vente/<int:pk>/', views.sale_update, name='sale_update'),
	path('supprimer-vente/<int:pk>/', views.sale_delete, name='sale_delete'),
	path('supprimer-item-vente/<int:pk>/', views.saleitem_delete, name='saleitem_delete'),
	path('detail-vente/<int:pk>/', views.sale_detail, name='sale_detail'),
	path('vente/<int:pk>/facture/', views.sale_invoice, name='sale_invoice'),

	#utilisateurs
	path('gestion-utilisateur/', views.gestion_utilisateur, name='gestion_utilisateur'),
	path('creer-utilisateur/', views.creer_utilisateur, name='creer_utilisateur'),
	path('update-utilisateur/<int:id>/', views.update_utilisateur, name='update_utilisateur'),
	path('supprimer-utilisateur/<int:user_id>/', views.supprimer_utilisateur, name='supprimer_utilisateur'),
	path('activer-desactiver-utilisateur/<int:id>/', views.activer_desactiver_utilisateur, name='activer_desactiver_utilisateur'),
]