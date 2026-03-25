from django.shortcuts import render, redirect, get_object_or_404
from django.template import loader
from django.db.models import Sum, F
from django.template.loader import render_to_string

from xhtml2pdf import pisa
from django.http import HttpResponse

from accounts.utils import redirect_user_by_role
from accounts.decorators import role_required

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.forms import modelform_factory

from sales.models import Sale, SaleItem
from sales.forms import SaleItemForm, SaleForm

from products.models import Product

from django.utils.timezone import now
from datetime import timedelta

from core.models import ShopSettings
import json

from django.core.paginator import Paginator

from decimal import Decimal

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
from reportlab.platypus import ListFlowable, ListItem

# Create your views here.
@login_required
@role_required('Caisse')
def home_caisse(request):
    template = loader.get_template('index_caisse.html')
    today = now().date()
    shop = ShopSettings.objects.first()
    total_sales = Sale.objects.filter(status='completed', user=request.user).aggregate(
        total_amount=Sum('total_amount'),
        total_profit=Sum('total_profit')
    )

    #Ventes récentes
    recent_sales = Sale.objects.filter(status='completed', user=request.user).order_by('-created_at')[:5]

    #Stock faible
    low_stock = Product.objects.filter(stock__lte=5)  # seuil = 5

    #Top produits vendus
    top_products = SaleItem.objects.values('product__name').annotate(
        total_qty=Sum('quantity')
    ).order_by('-total_qty')[:5]

    # 7 derniers jours
    last_7_days = []
    labels = []
    amounts = []

    for i in range(7):
        day = today - timedelta(days=i)
        total = Sale.objects.filter(
            status='completed',
            created_at__date=day,
            user = request.user
        ).aggregate(Sum('total_amount'))['total_amount__sum'] or 0

        labels.append(day.strftime("%d/%m"))
        amounts.append(float(total))

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
        'session_expiry': request.session.get_expiry_age(),
        'labels': json.dumps(labels[::-1]),
        'amounts': json.dumps(amounts[::-1]),
    }
    return HttpResponse(template.render(context, request))


@login_required
@role_required('Caisse')
def sale_list_caisse(request):
    template = loader.get_template('sale_list_caisse.html')
    sales = Sale.objects.filter(user = request.user, status='completed').order_by('-created_at')
    shop = ShopSettings.objects.first()

    sale_pagination = Paginator(sales, 10)
    pages_sale = request.GET.get('pages_sale')
    sale_pages = sale_pagination.get_page(pages_sale)

    context = {
        'sales':sale_pages,
        'shop':shop,
    }
    return HttpResponse(template.render(context, request))


@login_required
@role_required('Caisse')
def sale_create_caisse(request):
    template = loader.get_template('sale_create_caisse.html')
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
        # Mise à jour infos client
        # Formulaire client
        sale_form = SaleForm(request.POST, instance=sale)
        if sale_form.is_valid():
            sale_form.save()

        # Formulaire Produit
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
                return redirect('sale_create_caisse')

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
@role_required('Caisse')
def sale_delete_caisse(request, pk):
    pass

@login_required
@role_required('Caisse')
def sale_detail_caisse(request, pk):
    template = loader.get_template('sale_detail_caisse.html')
    sale = get_object_or_404(Sale, pk=pk, user=request.user)
    items = sale.items.all()
    shop = ShopSettings.objects.first()

    context = {
        'sale':sale,
        'items':items,
        'shop':shop,
    }
    return HttpResponse(template.render(context, request))

@login_required
@role_required('Caisse')
def sale_form_caisse(request, pk):
    template = loader.get_template('sale_form_caisse.html')

    sale = get_object_or_404(Sale, pk=pk, user=request.user)

    SaleForm = modelform_factory(Sale, fields=['user'])

    if request.method == "POST":
        form = SaleForm(request.POST, instance=sale)
        if form.is_valid():
            form.save()
            messages.success(request, "Vente modifiée.")
            return redirect('sale_detail_caisse', pk=sale.id)
    else:
        form = SaleForm(instance=sale)
    context = {
        'form':form
    }
    return HttpResponse(template.render(context, request))

@login_required
@role_required('Caisse')
def sale_invoice_caisse(request, pk):
    template = loader.get_template('sale_invoice_caisse.html')
    sale = get_object_or_404(Sale, pk=pk, status='completed', user=request.user)
    shop = ShopSettings.objects.first()

    # Charger le template
    html = render_to_string('sale_invoice.html', {'sale': sale, 'shop':shop })

    # Créer le PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'filename="facture_vente_{sale.id}.pdf"'

    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse('Erreur lors de la génération de la facture')

    return response

@login_required
@role_required('Caisse')
def saleitem_confirm_delete_caisse(request, pk):
    template = loader.get_template('saleitem_confirm_delete_caisse.html')
    # Récupérer l'item
    item = get_object_or_404(SaleItem, id=pk)

    # Récupérer la vente avant suppression
    sale_id = item.sale.id

    if request.method == "POST":
        item.delete()  # Ton delete() remet déjà le stock
        messages.success(request, "Produit retiré de la vente.")
        return redirect('sale_create_caisse')
    context = {
        'item':item
    }
    return HttpResponse(template.render(context, request))

@login_required
@role_required('Caisse')
def sale_finalize_caisse(request):
    sale_id = request.session.get('sale_id')

    if not sale_id:
        return redirect('sale_create_caisse')

    sale = get_object_or_404(Sale, id=sale_id)

    sale.status = 'completed'
    sale.save()
    # Supprimer la session
    del request.session['sale_id']

    messages.success(request, "Vente finalisée avec succès.")
    return redirect('sale_list_caisse')

@login_required
@role_required('Caisse')
def gestion_produit(request):
    template = loader.get_template('gestion_produit.html')
    products = Product.objects.all().order_by('-created_at')
    shop = ShopSettings.objects.first()

    product_pagination = Paginator(products, 10)
    pages_product = request.GET.get('pages_product')
    product_pages = product_pagination.get_page(pages_product)

    context = {
        'produits':product_pages,
        'shop':shop
    }
    return HttpResponse(template.render(context, request))

@login_required
@role_required('Caisse')
def sale_invoice_pos_caisse(request, pk):
    template = loader.get_template('sale_invoice_pos_caisse.html')
    sale = get_object_or_404(
        Sale,
        pk=pk,
        status='completed',
        user=request.user
    )

    shop = ShopSettings.objects.first()

    # html = render_to_string(
    #     'sale_invoice_pos_caisse.html',
    #     {'sale': sale, 'shop': shop}
    # )

    # response = HttpResponse(content_type='application/pdf')
    # response['Content-Disposition'] = f'filename="ticket_{sale.id}.pdf"'

    # pisa.CreatePDF(html, dest=response)
    context = {
        'sale':sale,
        'shop':shop,
    }
    return HttpResponse(template.render(context, request))

@login_required
@role_required('Caisse')
def generate_invoice(request, pk):
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
        elements.append(Image(shop.logo.path, width=0.5*inch, height=0.5*inch))

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

def test():
    pass