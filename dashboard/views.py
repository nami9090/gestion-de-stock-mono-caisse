from django.shortcuts import render
from django.db.models import Sum, F, Count
from accounts.decorators import role_required
from django.contrib.auth.decorators import login_required

from sales.models import Sale, SaleItem
from core.models import ShopSettings
from products.models import Product
from django.utils.timezone import now
from datetime import timedelta
from django.utils import timezone

from django.db.models.functions import TruncDay

from restaurent.models import RestaurantTable
from factures.models import Facture
from customers.models import Customer
from core.models import ShopSettings
from paiements.models import Paiement

# Create your views here.
@login_required
@role_required('Admin')
def dashboard_admin(request):
	shop = ShopSettings.objects.first()
	today = timezone.now().date()

	# =====================================
	# GLOBAL STATS
	# =====================================
	total_sales = Sale.objects.count()
	total_customers = Customer.objects.count()
	total_products = Product.objects.count()
	total_tables = RestaurantTable.objects.count()

	# =====================================
	# SALES TODAY
	# =====================================
	ventes_jour = Sale.objects.filter(
		created_at__date=today,
		status='completed'
	)
	chiffre_affaire_jour = ventes_jour.aggregate(
		total=Sum('total_amount')
	)['total'] or 0
	profit_jour = ventes_jour.aggregate(
		total=Sum('total_profit')
	)['total'] or 0

	# =====================================
	# FACTURES
	# =====================================
	factures_impayees = Facture.objects.filter(
		status__in=['issued', 'partial']
	).count()

	total_impaye = Facture.objects.filter(
		status__in=['issued', 'partial']
	).aggregate(
		total=Sum('total')
	)['total'] or 0

	# =====================================
	# COMMANDES RESTAURANT
	# =====================================
	commandes_en_cours = Sale.objects.filter(
		is_restaurant_order=True,
		order_status__in=['pending', 'sent', 'preparing']
	).count()

	commandes_pretes = Sale.objects.filter(
		is_restaurant_order=True,
		order_status='ready'
	).count()

	# =====================================
	# TABLES
	# =====================================
	tables_libres = RestaurantTable.objects.filter(
		status='free'
	).count()

	tables_occupees = RestaurantTable.objects.filter(
		status='occupied'
	).count()

	# =====================================
	# RECENT SALES
	# =====================================
	recent_sales = Sale.objects.select_related(
		'customer',
		'user'
	).order_by('-created_at')[:5]

	# =====================================
	# TOP PRODUCTS
	# =====================================
	top_products = Product.objects.order_by(
		'-stock'
	)[:5]

	# =====================================
	# GRAPH SALES LAST 7 DAYS
	# =====================================
	last_7_days = timezone.now() - timedelta(days=7)

	sales_chart = Sale.objects.filter(
		created_at__gte=last_7_days,
		status='completed'
	).annotate(
		day=TruncDay('created_at')
	).values('day').annotate(
		total=Sum('total_amount')
	).order_by('day')

	chart_labels = [
		item['day'].strftime('%d/%m')
		for item in sales_chart
	]

	chart_data = [
		float(item['total'])
		for item in sales_chart
	]

	# =====================================
	# PAYMENT METHODS
	# =====================================
	paiement_cash = Paiement.objects.filter(
		mode_paiement='cash'
	).count()

	paiement_mobile = Paiement.objects.filter(
		mode_paiement='mobile_money'
	).count()

	paiement_card = Paiement.objects.filter(
		mode_paiement='card'
	).count()

	context = {
		'shop': shop,

		# stats
		'total_sales': total_sales,
		'total_customers': total_customers,
		'total_products': total_products,
		'total_tables': total_tables,

		# finance
		'chiffre_affaire_jour': chiffre_affaire_jour,
		'profit_jour': profit_jour,
		'factures_impayees': factures_impayees,
		'total_impaye': total_impaye,

		# restaurant
		'commandes_en_cours': commandes_en_cours,
		'commandes_pretes': commandes_pretes,
		'tables_libres': tables_libres,
		'tables_occupees': tables_occupees,

		# data
		'recent_sales': recent_sales,
		'top_products': top_products,

		# chart
		'chart_labels': chart_labels,
		'chart_data': chart_data,

		# paiements
		'paiement_cash': paiement_cash,
		'paiement_mobile': paiement_mobile,
		'paiement_card': paiement_card,
	}
	return render(request, 'dashboard.html', context)

@login_required
@role_required('Caisse')
def dashboard_caisse(request):
	shop = ShopSettings.objects.first()
	today = now().date()
	ventes_jour = Sale.objects.filter(
		created_at__date=today,
		status='completed'
	)

	total_ventes = ventes_jour.aggregate(
		total=Sum('total_amount')
	)['total'] or 0

	nombre_ventes = ventes_jour.count()

	commandes_restaurant = Sale.objects.filter(
		is_restaurant_order=True,
		status='draft'
	).count()

	factures_impayees = Facture.objects.filter(
		status__in=['issued']
	).count()

	produits_stock_faible = Product.objects.filter(
		stock__lte=5
	)[:10]

	ventes_recentes = Sale.objects.select_related(
		'customer',
		'restaurant_table'
	).order_by('-created_at')[:5]

	tables_occupees = RestaurantTable.objects.filter(
		status='occupee'
	).count()

	clients_total = Customer.objects.count()

	context = {
		'total_ventes': total_ventes,
		'nombre_ventes': nombre_ventes,
		'commandes_restaurant': commandes_restaurant,
		'factures_impayees': factures_impayees,
		'produits_stock_faible': produits_stock_faible,
		'ventes_recentes': ventes_recentes,
		'tables_occupees': tables_occupees,
		'clients_total': clients_total,
		'shop':shop,
	}
	return render(request, 'dashboard_caisse.html', context)


@login_required
@role_required('Serveur')
def dashboard_serveur(request):

	shop = ShopSettings.objects.first()

	today = timezone.now().date()

	# =====================================
	# TABLES
	# =====================================
	tables = RestaurantTable.objects.select_related(
		'customer'
	).all().order_by('name')

	tables_libres = tables.filter(
		status='free'
	).count()

	tables_occupees = tables.filter(
		status='occupied'
	).count()

	# =====================================
	# COMMANDES
	# =====================================
	commandes = Sale.objects.filter(
		is_restaurant_order=True,
		status='draft'
	).select_related(
		'restaurant_table',
		'customer',
		'user'
	).prefetch_related(
		'items'
	).order_by('-created_at')

	commandes_pretes = Sale.objects.filter(
		is_restaurant_order=True,
		order_status='ready'
	).count()

	commandes_en_cours = Sale.objects.filter(
		is_restaurant_order=True,
		order_status__in=[
			'pending',
			'sent',
			'preparing'
		]
	).count()

	# =====================================
	# FACTURES
	# =====================================
	factures_du_jour = Facture.objects.filter(
		created_at__date=today
	)

	total_ventes = factures_du_jour.aggregate(
		total=Sum('total')
	)['total'] or 0

	factures_impayees = Facture.objects.filter(
		status__in=[
			'issued',
			'partial'
		]
	).count()

	# =====================================
	# CONTEXT
	# =====================================
	context = {

		# shop
		'shop': shop,

		# tables
		'tables': tables,
		'tables_libres': tables_libres,
		'tables_occupees': tables_occupees,

		# commandes
		'commandes': commandes[:10],
		'commandes_pretes': commandes_pretes,
		'commandes_en_cours': commandes_en_cours,

		# finances
		'total_ventes': total_ventes,
		'factures_impayees': factures_impayees,

	}

	return render(
		request,
		'dashboard_serveur.html',
		context
	)


from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone


@login_required
@role_required('Cuisine')
def dashboard_cuisine(request):

	# Commandes envoyées ou en préparation
	commandes = Sale.objects.filter(
		is_restaurant_order=True,
		order_status__in=['sent', 'preparing']
	).select_related(
		'restaurant_table',
		'customer'
	).prefetch_related(
		'items__product'
	).order_by('created_at')

	context = {
		'commandes': commandes
	}
	return render(request,'dashboard_cuisine.html',context)