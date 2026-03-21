from django.shortcuts import render, redirect, get_object_or_404
from django.template import loader
from django.http import HttpResponse
from django.forms import modelform_factory
from django.contrib.auth.models import User, Group
from django.template.loader import render_to_string

from xhtml2pdf import pisa
from django.core.paginator import Paginator
from products.models import Product, Category
from products.forms import ProductForm, CategoryForm

from suppliers.models import Supplier
from suppliers.forms import SupplierForm

from stock.models import StockEntry
from stock.forms import StockEntryForm

from sales.models import Sale, SaleItem
from sales.forms import SaleForm, SaleItemForm

from accounts.utils import redirect_user_by_role
from accounts.forms import UserCreateForm
from accounts.models import UserActivityLog

from django.contrib import messages

from .models import ShopSettings
from .forms import ShopSettingsForm

from django.db.models import Sum, F
from accounts.decorators import role_required
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout

### Facture avec ReportLab
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
)
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import A4
from reportlab.platypus import HRFlowable
from reportlab.lib.enums import TA_RIGHT, TA_LEFT
from reportlab.platypus import KeepTogether
from io import BytesIO
from datetime import datetime
from decimal import Decimal
from reportlab.platypus import ListFlowable, ListItem

# Create your views here.
@login_required
@role_required('Admin')
def shop_settings_view(request):
    template = loader.get_template('shop_settings_view.html')
    # On récupère la première instance ou on en crée une
    shop, created = ShopSettings.objects.get_or_create(id=1)
    
    if request.method == 'POST':
        form = ShopSettingsForm(request.POST, instance=shop)
        if form.is_valid():
            form.save()
            messages.success(request, "Paramètres du magasin mis à jour avec succès !")
            return redirect('shop_settings_view')
        else:
            messages.warning(request, "Veuillez corriger les erreurs ci-dessous.")
    else:
        form = ShopSettingsForm(instance=shop)
    context = {
        'form':form
    }
    return HttpResponse(template.render(context, request))

@login_required
@role_required('Admin')
def home(request):
    template = loader.get_template('index.html')
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
    return HttpResponse(template.render(context, request))

@login_required
@role_required('Admin')
def gestion_utilisateur(request):
    template = loader.get_template('gestion_utilisateur.html')
    utilisateurs = User.objects.all().order_by('username')

    user_pagination = Paginator(utilisateurs, 10)
    pages_user = request.GET.get('pages_user')
    user_pages = user_pagination.get_page(pages_user)

    context = {
        'utilisateurs':user_pages
    }
    return HttpResponse(template.render(context, request))

@login_required
@role_required('Admin')
def creer_utilisateur(request):
    template = loader.get_template('form_utilisateur.html')
    if request.method == 'POST':
        form = UserCreateForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"L'utilisateur {user.username} a été créé avec succès !")
            redirect('gestion_utilisateur')
        else:
            messages.error(request, "Erreur : le formulaire est invalide.")
    else:
        form = UserCreateForm()
        redirect('gestion_utilisateur')
    context = {
        'form':form
    }
    return HttpResponse(template.render(context, request))

@login_required
@role_required('Admin')
def update_utilisateur(request, id):
    template = loader.get_template('form_utilisateur.html')
    user = get_object_or_404(User, pk=id)
    if request.method == 'POST':
        form = UserCreateForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, f"L'utilisateur {user.username} a été updated avec succès !")
            redirect('gestion_utilisateur')
        else:
            messages.error(request, "Erreur : le formulaire est invalide.")
    else:
        form = UserCreateForm(instance=user)
        redirect('gestion_utilisateur')
    context = {
        'form':form
    }
    return HttpResponse(template.render(context, request))

@login_required
@role_required('Admin')
def supprimer_utilisateur(request, user_id):
    user = get_object_or_404(User, id=user_id)

    if request.user == user:
        messages.error(request, "Vous ne pouvez pas supprimer votre propre compte !")
        return redirect('gestion_utilisateur')

    user.delete()
    messages.success(request, f"L'utilisateur {user.username} a été supprimé avec succès !")
    return redirect('gestion_utilisateur')

@login_required
@role_required('Admin')
def activer_desactiver_utilisateur(request, id):
    user = get_object_or_404(User, pk=id)
    user.is_active = not user.is_active
    user.save()
    messages.success(request, f"L'utilisateur {user.username} devient {user.is_active}")
    return redirect('gestion_utilisateur')


def product_list(request):
    template = loader.get_template('product_list.html')
    products = Product.objects.all().order_by('-created_at')
    shop = ShopSettings.objects.first()
    context = {
        'produits':products,
        'shop':shop
    }
    return HttpResponse(template.render(context, request))

@login_required
@role_required('Admin')
def product_create(request):
    template = loader.get_template('product_form.html')
    form = ProductForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('product_list')
    context = {
        'form':form
    }
    return HttpResponse(template.render(context, request))

@login_required
@role_required('Admin')
def product_update(request, pk):
    template = loader.get_template('product_form.html')
    product = get_object_or_404(Product, pk=pk)
    form = ProductForm(request.POST or None, instance=product)
    if form.is_valid():
        form.save()
        return redirect('product_list')
    context = {
        'form':form
    }
    return HttpResponse(template.render(context, request))

@login_required
@role_required('Admin')
def product_delete(request, pk):
    template = loader.get_template('product_confirm_delete.html')
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.delete()
        return redirect('product_list')
    context = {
        'product':product
    }
    return HttpResponse(template.render(context, request))

@login_required
@role_required('Admin')
def product_detail(request, pk):
    template = loader.get_template('product_details.html')
    product = get_object_or_404(Product, pk=pk)
    context = {
        'product':product
    }
    return HttpResponse(template.render(context, request))

@login_required
@role_required('Admin')
def category_list(request):
    template = loader.get_template('category_list.html')
    categories = Category.objects.all().order_by('name')
    context = {
        'categories':categories
    }
    return HttpResponse(template.render(context, request))

@login_required
@role_required('Admin')
def category_create(request):
    template = loader.get_template('category_form.html')
    form = CategoryForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('category_list')
    context = {
        'form':form
    }
    return HttpResponse(template.render(context, request))

@login_required
@role_required('Admin')
def category_update(request, pk):
    template = loader.get_template('category_form.html')
    categorie = get_object_or_404(Category, pk=pk)
    form = ProductForm(request.POST or None, instance=categorie)
    if form.is_valid():
        form.save()
        return redirect('category_list')
    context = {
        'form':form
    }
    return HttpResponse(template.render(context, request))

@login_required
@role_required('Admin')
def category_delete(request, pk):
    template = loader.get_template('category_confirm_delete.html')
    categorie = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        categorie.delete()
        return redirect('category_list')
    context = {
        'category':categorie
    }
    return HttpResponse(template.render(context, request))

@login_required
@role_required('Admin')
def supplier_list(request):
    template = loader.get_template('supplier_list.html')
    suppliers = Supplier.objects.all()
    context = {
        'suppliers':suppliers
    }
    return HttpResponse(template.render(context, request))

@login_required
@role_required('Admin')
def supplier_create(request):
    template = loader.get_template('supplier_form.html')
    form = SupplierForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('supplier_list')
    context = {
        'form':form
    }
    return HttpResponse(template.render(context, request))

@login_required
@role_required('Admin')
def supplier_update(request, pk):
    template = loader.get_template('supplier_form.html')
    supplier = get_object_or_404(Supplier, pk=pk)
    form = SupplierForm(request.POST or None, instance=supplier)
    if form.is_valid():
        form.save()
        return redirect('supplier_list')
    context = {
        'form':form
    }
    return HttpResponse(template.render(context, request))

@login_required
@role_required('Admin')
def supplier_delete(request, pk):
    template = loader.get_template('supplier_confirm_delete.html')
    supplier = get_object_or_404(Supplier, pk=pk)
    if request.method == 'POST':
        supplier.delete()
        return redirect('supplier_list')
    context = {
        'supplier':supplier
    }
    return HttpResponse(template.render(context, request))

@login_required
@role_required('Admin')
def stock_list(request):
    template = loader.get_template('stock_list.html')
    stocks = StockEntry.objects.select_related('product', 'supplier', 'user').order_by('-date')
    context = {
        'stocks':stocks
    }
    return HttpResponse(template.render(context, request))

@login_required
@role_required('Admin')
def stock_create(request):
    template = loader.get_template('stock_form.html')
    form = StockEntryForm(request.POST or None)
    if form.is_valid():
        stock_entry = form.save(commit=False)
        stock_entry.user = request.user
        stock_entry.save()
        return redirect('stock_list')
    context = {
        'form':form
    }
    return HttpResponse(template.render(context, request))

@login_required
@role_required('Admin')
def sale_list(request):
    template = loader.get_template('sale_list.html')
    sales = Sale.objects.filter(status='completed').order_by('-created_at')
    shop = ShopSettings.objects.first()
    context = {
        'sales':sales,
        'shop':shop,
    }
    return HttpResponse(template.render(context, request))


@login_required
@role_required('Admin')
def sale_invoice(request, pk):
    sale = get_object_or_404(Sale, id=pk)
    shop = ShopSettings.objects.first()

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []

    styles = getSampleStyleSheet()

    right_style = ParagraphStyle(
        name="RightAlign",
        parent=styles["Normal"],
        alignment=TA_RIGHT
    )

    # =========================
    # HEADER
    # =========================
    if shop.logo:
        elements.append(Image(shop.logo.path, width=1.5*inch, height=1.5*inch))

    elements.append(Paragraph(f"<b>{shop.name}</b>", styles["Heading1"]))
    elements.append(Paragraph(shop.address, styles["Normal"]))
    elements.append(Paragraph(f"Tél: {shop.phone}", styles["Normal"]))
    elements.append(Spacer(1, 10))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
    elements.append(Spacer(1, 15))

    # =========================
    # INFO CLIENT + FACTURE
    # =========================
    invoice_number = f"FACT-{sale.id:05d}"
    date_now = sale.created_at.strftime("%d/%m/%Y")

    info_data = [[
        Paragraph(
            f"<b>Client :</b><br/>{sale.customer_name}<br/>{sale.customer_phone}",
            styles["Normal"]
        ),
        Paragraph(
            f"<b>Facture N° :</b> {invoice_number}<br/><b>Date :</b> {date_now}",
            right_style
        )
    ]]

    info_table = Table(info_data, colWidths=[3.5*inch, 2.5*inch])
    elements.append(info_table)
    elements.append(Spacer(1, 20))

    # =========================
    # TABLE PRODUITS
    # =========================
    data = [["Produit", "Qté", "Prix U.", "Total"]]

    total_general = Decimal("0.00")

    for item in sale.items.all():
        total = item.quantity * item.purchase_price
        total_general += total

        data.append([
            item.product.name,
            str(item.quantity),
            f"{item.purchase_price:,.0f} {shop.currency}",
            f"{total:,.0f} {shop.currency}",
        ])

    table = Table(data, colWidths=[2.5*inch, 1*inch, 1.2*inch, 1.2*inch])

    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.black),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 20))

    # =========================
    # TOTALS
    # =========================
    tva_rate = Decimal(shop.tva if shop.tva else 0)
    tva = total_general * (tva_rate / Decimal("100"))
    grand_total = total_general + tva

    totals_data = [
        ["Sous-total :", f"{total_general:,.0f} {shop.currency}"],
        [f"TVA ({tva_rate}%) :", f"{tva:,.0f} {shop.currency}"],
        ["TOTAL :", f"{grand_total:,.0f} {shop.currency}"],
    ]

    totals_table = Table(totals_data, colWidths=[3.7*inch, 1.5*inch])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('LINEABOVE', (0, 2), (-1, 2), 1, colors.black),
    ]))

    elements.append(totals_table)
    elements.append(Spacer(1, 30))

    # =========================
    # FOOTER
    # =========================
    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph("Merci pour votre confiance :)", styles["Normal"]))

    doc.build(elements)

    pdf = buffer.getvalue()
    buffer.close()

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="facture_{sale.id}.pdf"'
    response.write(pdf)

    return response

@login_required
@role_required('Admin')
def generate_invoice(request, pk):
    pass

@login_required
@role_required('Admin')
def sale_create(request):
    template = loader.get_template('sale_create.html')
    # Récupérer ou créer vente en session
    sale_id = request.session.get('sale_id')
    shop = ShopSettings.objects.first()
    if sale_id:
        try:
            sale = Sale.objects.get(id=sale_id)
        except Sale.DoesNotExist:
            sale = Sale.objects.create(user=request.user)
            request.session['sale_id'] = sale.id
    else:
        sale = Sale.objects.create(user=request.user)
        request.session['sale_id'] = sale.id

    sale_form = SaleForm(instance=sale)
    form = SaleItemForm()

    # Ajouter un produit
    if request.method == "POST":
        sale_form = SaleForm(request.POST, instance=sale)
        if sale_form.is_valid():
            sale_form.save()

        form = SaleItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.sale = sale

            # remplir automatiquement les prix
            item.selling_price = item.product.selling_price
            item.purchase_price = item.product.purchase_price

            # Vérification stock
            if item.quantity > item.product.stock:
                messages.warning(request, "Stock insuffisant.")
            else:
                item.save()
                messages.success(request, "Produit ajouté à la vente.")
                return redirect('sale_create')

    items = sale.items.all()

    context = {
        'sale': sale,
        'items': items,
        'sale_form':sale_form,
        'form': form,
        'shop':shop
    }
    return HttpResponse(template.render(context, request))


@login_required
@role_required('Admin')
def sale_finalize(request):
    sale_id = request.session.get('sale_id')

    if not sale_id:
        return redirect('sale_create')

    sale = get_object_or_404(Sale, id=sale_id)

    sale.status = 'completed'
    sale.save()
    # Supprimer la session
    del request.session['sale_id']

    messages.success(request, "Vente finalisée avec succès.")
    return redirect('sale_list')


@login_required
@role_required('Admin')
def sale_update(request, pk):
    template = loader.get_template('sale_form.html')

    sale = get_object_or_404(Sale, pk=pk)

    SaleForm = modelform_factory(Sale, fields=['user', 'customer_name', 'customer_phone'])


    if request.method == "POST":
        form = SaleForm(request.POST, instance=sale)
        if form.is_valid():
            form.save()
            messages.success(request, "Vente modifiée.")
            # return redirect('sale_detail', pk=sale.id)
            return redirect('sale_list')
    else:
        form = SaleForm(instance=sale)
    context = {
        'form':form
    }
    return HttpResponse(template.render(context, request))


@login_required
@role_required('Admin')
def sale_delete(request, pk):
    template = loader.get_template('sale_delete.html')
    sale = get_object_or_404(Sale, pk=pk)

    # Empêcher suppression si finalisée
    if sale.status == 'completed':
        messages.error(request, "Impossible de supprimer une vente finalisée.")
        return redirect('sale_list')

    if request.method == "POST":

        #Supprimer les items (stock remis automatiquement)
        for item in sale.items.all():
            item.delete()

        #Supprimer la vente
        sale.delete()

        #Nettoyer la session si nécessaire
        if request.session.get('sale_id') == sale.id:
            del request.session['sale_id']

        messages.success(request, "Vente annulée avec succès.")
        return redirect('sale_create')
    context = {
        'sale':sale
    }
    return HttpResponse(template.render(context, request))


@login_required
@role_required('Admin')
def saleitem_delete(request, pk):
    template = loader.get_template('saleitem_confirm_delete.html')
    # Récupérer l'item
    item = get_object_or_404(SaleItem, id=pk)

    # Récupérer la vente avant suppression
    sale_id = item.sale.id

    if request.method == "POST":
        item.delete()  # Ton delete() remet déjà le stock
        messages.success(request, "Produit retiré de la vente.")
        return redirect('sale_create')
    context = {
        'item':item
    }
    return HttpResponse(template.render(context, request))


@login_required
@role_required('Admin')
def sale_detail(request, pk):
    template = loader.get_template('sale_detail.html')
    sale = get_object_or_404(Sale, pk=pk)
    items = sale.items.all()
    shop = ShopSettings.objects.first()
    context = {
        'sale':sale,
        'items':items,
        'shop':shop,
    }
    return HttpResponse(template.render(context, request))
