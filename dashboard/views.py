from django.shortcuts import render
from django.db.models import Sum, F
from accounts.decorators import role_required
from django.contrib.auth.decorators import login_required

from sales.models import Sale, SaleItem
from core.models import ShopSettings
from products.models import Product

# Create your views here.
@login_required
@role_required('Admin','Caisse')
def dashboard(request):
    shop = ShopSettings.objects.first()
    total_sales = Sale.objects.filter(status='completed').aggregate(
        total_amount=Sum('total_amount'),
        total_profit=Sum('total_profit')
    )
    #Ventes récentes
    recent_sales = Sale.objects.filter(status='completed').order_by('-created_at')[:5]
    #Stock faible
    low_stock = Product.objects.filter(stock__lte=5)  # seuil = 5
    #Top produits vendus
    top_products = SaleItem.objects.values('product__name').annotate(
        total_qty=Sum('quantity')
    ).order_by('-total_qty')[:5]
    #Vente en attente
    #sales = Sale.objects.filter(status='draft').order_by('-created_at')
    items = SaleItem.objects.filter(sale__status='draft')
    sale_count = items.count()
    context = {
        'total_sales': total_sales,
        'recent_sales': recent_sales,
        'low_stock': low_stock,
        'top_products': top_products,
        'sale_count':sale_count,
        'shop':shop,
    }
    return render(request, 'dashboard.html', context)