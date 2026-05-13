from django.urls import path
from . import views

app_name = "products"

urlpatterns = [
	##Products
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
]
