from django.urls import path
from . import views

app_name='stock'

urlpatterns = [
    #Stocks
	path('stock-liste/', views.stock_list, name='stock_list'),
	path('ajouter-stock/', views.stock_create, name='stock_create'),
]
