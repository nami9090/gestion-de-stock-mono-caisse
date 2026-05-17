from django.urls import path
from . import views

app_name = 'sale'

urlpatterns = [
    #Sales
	path('vente-liste/', views.sale_list, name='sale_list'),
	path('creer-vente/', views.sale_create, name='sale_create'),
	path('finaliser-vente/', views.sale_finalize, name='sale_finalize'),
	path('update-vente/<int:pk>/', views.sale_update, name='sale_update'),
	path('supprimer-vente/<int:pk>/', views.sale_delete, name='sale_delete'),
	path('supprimer-item-vente/<int:pk>/', views.saleitem_delete, name='saleitem_delete'),
	path('detail-vente/<int:pk>/', views.sale_detail, name='sale_detail'),
	path('vente/<int:pk>/facture/', views.sale_invoice, name='sale_invoice'),
    path('facture-pos/<int:pk>/', views.sale_invoice_pos, name='sale_invoice_pos'),

    path('rapport-vente/', views.closing_report_view, name='closing_report_view'),
    path("closing-pdf/", views.download_closing_pdf, name="download_closing_pdf"),

    path('restaurant/create/<int:table_id>/', views.create_restaurant_sale, name='create_restaurant_sale'),

    path('restaurant/status/<int:sale_id>/<str:status>/', views.update_order_status,name='update_order_status'),

    path('<int:sale_id>/add-item/', views.add_sale_item,name='add_sale_item'),

    path('<int:sale_id>/send/', views.send_to_kitchen, name='send_to_kitchen'),

    path('<int:sale_id>/mark-preparing/', views.mark_preparing, name='mark_preparing'),
    path('<int:sale_id>/mark-ready/', views.mark_ready, name='mark_ready'),

]
