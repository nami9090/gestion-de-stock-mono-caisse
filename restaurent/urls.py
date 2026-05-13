from django.urls import path
from . import views

app_name = 'restaurant'

urlpatterns = [
    path('', views.table_list, name='table_list'),
    path('table/create/', views.table_create,name='table_create'),
    path('table/<int:pk>/update/', views.table_update, name='table_update'),
    path('table/<int:pk>/delete/', views.table_delete, name='table_delete'),
    path('table/<int:pk>/detail/', views.table_detail, name='table_detail'),
    path('table/<int:pk>/open/', views.open_table, name='open_table'),
    path('table/<int:pk>/close/', views.close_table, name='close_table'),

    path('sale/<int:sale_id>/retirer/', views.delete_sale, name='delete_sale'),
]