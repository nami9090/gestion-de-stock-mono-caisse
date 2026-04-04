from django.urls import path
from . import views

app_name = "user"

urlpatterns = [
	path('', views.login_view, name='login'),
	path('logout-session/', views.logout_view, name='logout'),
	
	#utilisateurs
	path('gestion-utilisateur/', views.gestion_utilisateur, name='gestion_utilisateur'),
	path('creer-utilisateur/', views.creer_utilisateur, name='creer_utilisateur'),
	path('update-utilisateur/<int:id>/', views.update_utilisateur, name='update_utilisateur'),
	path('supprimer-utilisateur/<int:user_id>/', views.supprimer_utilisateur, name='supprimer_utilisateur'),
	path('activer-desactiver-utilisateur/<int:id>/', views.activer_desactiver_utilisateur, name='activer_desactiver_utilisateur'),
]