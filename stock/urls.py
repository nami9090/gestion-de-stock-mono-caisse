from django.urls import path
from . import views

app_name='stock'

urlpatterns = [
    #Stocks
	path('list/', views.stock_list, name='stock_list'),
	path('ajouter/', views.stock_create, name='stock_create'),
	path('<int:pk>/update/', views.stock_update, name='stock_update'),
	path('<int:pk>/delete/', views.stock_delete, name='stock_delete'),
	path('<int:pk>/detail/',views.stock_detail, name='stock_detail'),
	path('global-rapport/', views.stock_report, name='stock_report'),
	path('month-report/', views.stock_monthly_report, name='stock_monthly_report'),
	path('inventory-report/', views.stock_inventory_report, name='stock_inventory_report'),
	path('inventory-pdf/', views.stock_inventory_pdf, name='stock_inventory_pdf'),
	path('inventory-excel', views.stock_inventory_excel, name='stock_inventory_excel'),
]
