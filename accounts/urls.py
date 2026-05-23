from django.urls import path
from . import views

app_name = "user"

urlpatterns = [
	path('', views.login_view, name='login'),
	path('logout-session/', views.logout_view, name='logout'),
	
	#utilisateurs
	path('user-list/', views.gestion_utilisateur, name='gestion_utilisateur'),
	path('user-form/', views.creer_utilisateur, name='creer_utilisateur'),
	path('<int:id>/user-update/', views.update_utilisateur, name='update_utilisateur'),
	path('<int:user_id>/user-delete/', views.supprimer_utilisateur, name='supprimer_utilisateur'),
	path('<int:id>/user-activate-deactivate/', views.activer_desactiver_utilisateur, name='activer_desactiver_utilisateur'),
	path('<int:id>/user-activity/', views.user_activity, name='user_activity'),
]