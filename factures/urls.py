from django.urls import path
from . import views

app_name = 'facture'

urlpatterns = [
    path('', views.facture_list, name='facture_list'),
    path('<int:pk>/details/', views.facture_detail, name='facture_detail'),
    path('create/', views.facture_create, name='facture_create'),
    path('<int:pk>/update/', views.facture_update, name='facture_update'),
    path('<int:pk>/delete/', views.facture_delete, name='facture_delete'),
]