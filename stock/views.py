from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.core.paginator import Paginator
from django.db.models import Q, Sum, F, Count

from django.utils.timezone import now
from datetime import datetime

from accounts.decorators import role_required
from django.contrib.auth.decorators import login_required

from .models import StockEntry
from .forms import StockEntryForm

from products.models import Product
from core.models import ShopSettings

from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

from openpyxl import Workbook

from products.models import Product


# ==============================
# LISTE DES ENTREES STOCK
# ==============================
@login_required
@role_required('Admin')
def stock_list(request):
    search = request.GET.get('search', '')
    stocks = StockEntry.objects.select_related(
        'product',
        'supplier',
        'user'
    ).order_by('-date')

    # ================= SEARCH =================
    if search:
        stocks = stocks.filter(
            Q(product__name__icontains=search) |
            Q(supplier__name__icontains=search)
        )

    # ================= PAGINATION =================
    paginator = Paginator(stocks, 20)
    page_number = request.GET.get('page')
    stocks = paginator.get_page(page_number)

    context = {
        'stocks': stocks,
        'search': search,
    }
    return render(request, 'stock_list.html', context)


# ==============================
# CREATION ENTREE STOCK
# ==============================
@login_required
@role_required('Admin')
def stock_create(request):
    if request.method == 'POST':
        form = StockEntryForm(request.POST)

        if form.is_valid():
            try:
                with transaction.atomic():

                    stock_entry = form.save(commit=False)
                    stock_entry.user = request.user
                    stock_entry.save()

                    # 🔥 AJOUT STOCK UNE SEULE FOIS
                    product = stock_entry.product
                    product.stock += stock_entry.quantity
                    product.save()

                    messages.success(request, "Stock ajouté avec succès.")
                    return redirect('stock:stock_list')

            except Exception as e:
                messages.error(request, f"Erreur : {str(e)}")

    else:
        form = StockEntryForm()

    return render(request, 'stock_form.html', {'form': form})

@login_required
@role_required('Admin')
def stock_update(request, pk):
    stock = get_object_or_404(StockEntry, pk=pk)

    if request.method == 'POST':
        form = StockEntryForm(request.POST, instance=stock)

        if form.is_valid():
            try:
                with transaction.atomic():
                    # récupérer valeur brute DB (TRÈS IMPORTANT)
                    old_stock = StockEntry.objects.select_related('product').get(pk=pk)

                    old_product = Product.objects.get(pk=old_stock.product_id)
                    old_quantity = old_stock.quantity

                    # retirer ancien stock
                    old_product.stock -= old_quantity
                    old_product.save()

                    # save form
                    updated_stock = form.save(commit=False)
                    updated_stock.user = request.user
                    updated_stock.save()

                    # IMPORTANT: recharger produit proprement
                    new_product = Product.objects.get(pk=updated_stock.product_id)
                    new_product.stock += updated_stock.quantity
                    new_product.save()

                    messages.success(request, "Stock mis à jour avec succès.")
                    return redirect('stock:stock_list')

            except Exception as e:
                messages.error(request, f"Erreur : {str(e)}")

    else:
        # IMPORTANT : form doit exister ici
        form = StockEntryForm(instance=stock)

    return render(request, 'stock_form.html', {
        'form': form,
        'stock': stock
    })

@login_required
@role_required('Admin')
def stock_delete(request, pk):
    stock = get_object_or_404(StockEntry, pk=pk)
    if request.method == 'POST':
        try:
            with transaction.atomic():
                product = stock.product
                # retirer stock
                product.stock -= stock.quantity
                product.save()
                stock.delete()
                messages.success(request, "Entrée stock supprimée avec succès.")
                return redirect('stock:stock_list')

        except Exception as e:
            messages.error(request, f"Erreur : {str(e)}")

    return render(request, 'stock_confirm_delete.html', {
        'stock': stock
    })

# ===========================
# DETAIL
# ===========================
@login_required
@role_required('Admin')
def stock_detail(request, pk):
    stock = get_object_or_404(
        StockEntry.objects.select_related(
            'product',
            'supplier',
            'user'
        ),
        pk=pk
    )

    return render(request,'stock_detail.html',{'stock': stock})

@login_required
@role_required('Admin')
def stock_report(request):
    products = Product.objects.all().order_by('name')
    shop = ShopSettings.objects.first()
    # stats globales
    total_products = products.count()
    total_stock_value = sum(p.stock_value for p in products)
    low_stock_products = products.filter(stock__lte=F('minimum_stock'))

    context = {
        'products': products,
        'total_products': total_products,
        'total_stock_value': total_stock_value,
        'low_stock_products': low_stock_products,
        'shop':shop,
    }

    return render(request, 'stock_report.html', context)


@login_required
@role_required('Admin')
def stock_monthly_report(request):
    month = request.GET.get('month')
    year = request.GET.get('year')
    today = now()
    if not month:
        month = today.month
    if not year:
        year = today.year
    stocks = StockEntry.objects.filter(
        date__month=month,
        date__year=year
    ).select_related('product', 'user')
    total_quantity = stocks.aggregate(total=Sum('quantity'))['total'] or 0
    context = {
        'stocks': stocks,
        'month': int(month),
        'year': int(year),
        'total_quantity': total_quantity,
    }

    return render(request, 'stock_monthly_report.html', context)


from django.db.models import Sum, F, FloatField, ExpressionWrapper

@login_required
@role_required('Admin')
def stock_inventory_report(request):
    shop = ShopSettings.objects.first()
    products = Product.objects.all()
    total_stock_items = products.aggregate(total=Sum('stock'))['total'] or 0
    low_stock = products.filter(stock__lte=F('minimum_stock'))

    # valeur stock totale
    total_value = sum(p.stock * p.selling_price for p in products)

    context = {
        'products': products,
        'total_stock_items': total_stock_items,
        'low_stock': low_stock,
        'total_value': total_value,
        'shop': shop,
    }
    return render(request, 'stock_inventory_report.html', context)



@login_required
@role_required('Admin')
def stock_inventory_pdf(request):

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="inventory_report.pdf"'

    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    products = Product.objects.all()

    y = height - 50

    # TITLE
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, y, "RAPPORT D'INVENTAIRE STOCK")
    y -= 30

    p.setFont("Helvetica", 10)
    p.drawString(50, y, f"Date: {now().strftime('%Y-%m-%d %H:%M')}")
    y -= 30

    # HEADER TABLE
    p.setFont("Helvetica-Bold", 10)
    p.drawString(50, y, "Produit")
    p.drawString(200, y, "Stock")
    p.drawString(280, y, "Min")
    p.drawString(340, y, "Prix")
    p.drawString(420, y, "Valeur")

    y -= 20

    total_value = 0

    p.setFont("Helvetica", 10)

    for product in products:

        value = product.stock * product.selling_price
        total_value += value

        if y < 50:
            p.showPage()
            y = height - 50

        p.drawString(50, y, str(product.name))
        p.drawString(200, y, str(product.stock))
        p.drawString(280, y, str(product.minimum_stock))
        p.drawString(340, y, str(product.selling_price))
        p.drawString(420, y, str(value))

        y -= 20

    # TOTAL
    y -= 20
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, f"TOTAL VALEUR STOCK: {total_value}")

    p.showPage()
    p.save()

    return response


@login_required
@role_required('Admin')
def stock_inventory_excel(request):

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="inventory_report.xlsx"'

    wb = Workbook()
    ws = wb.active
    ws.title = "Inventory"

    # HEADER
    ws.append([
        "Produit",
        "Stock",
        "Minimum",
        "Prix vente",
        "Valeur stock"
    ])

    products = Product.objects.all()

    for p in products:
        ws.append([
            p.name,
            p.stock,
            p.minimum_stock,
            p.selling_price,
            p.stock * p.selling_price
        ])

    wb.save(response)

    return response