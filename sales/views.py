from django.forms import modelform_factory
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from accounts.decorators import role_required
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from .models import Sale, SaleItem
from .forms import SaleForm, SaleItemForm

from products.models import Product
from customers.models import Customer

from core.models import ShopSettings
from .sale_report import closing_report
from factures.models import Facture
from restaurent.models import RestaurantTable

from .pdf_closing import generate_closing_pdf

from django.utils import timezone
from django.db.models import Q

### Facture avec ReportLab
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
)
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import A4
from reportlab.platypus import HRFlowable
from reportlab.lib.enums import TA_RIGHT, TA_LEFT, TA_CENTER
from reportlab.platypus import KeepTogether
from io import BytesIO
from datetime import datetime
from decimal import Decimal
from reportlab.platypus import ListFlowable, ListItem

# Create your views here.
@login_required
@role_required('Admin','Caisse')
def sale_list(request):
    if request.user.is_superuser:
        sales = Sale.objects.filter(
            status='completed',
        ).select_related('facture', 'customer', 'user').order_by('-created_at')
    else:
        sales = Sale.objects.filter(
            status='completed',
            # user=request.user
        ).select_related('facture', 'customer', 'user').order_by('-created_at')
    shop = ShopSettings.objects.first()
    context = {
        'sales':sales,
        'shop':shop,
    }
    return render(request, 'sale_list.html', context)


@login_required
@role_required('Admin', 'Caisse')
def sale_invoice(request, pk):

    sale = get_object_or_404(
        Sale.objects.select_related(
            'customer',
            'facture',
            'restaurant_table',
            'user'
        ),
        id=pk
    )

    shop = ShopSettings.objects.first()

    # =========================
    # FACTURE
    # =========================
    facture = getattr(sale, 'facture', None)

    # =========================
    # PDF BUFFER
    # =========================
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=18
    )

    elements = []

    styles = getSampleStyleSheet()

    right_style = ParagraphStyle(
        name="RightAlign",
        parent=styles["Normal"],
        alignment=TA_RIGHT
    )

    center_style = ParagraphStyle(
        name="Center",
        parent=styles["Normal"],
        alignment=TA_CENTER
    )

    # =========================
    # HEADER
    # =========================
    if shop.logo:
        try:
            elements.append(
                Image(
                    shop.logo.path,
                    width=1.2 * inch,
                    height=1.2 * inch
                )
            )
        except:
            pass

    elements.append(
        Paragraph(
            f"<b>{shop.name}</b>",
            styles["Title"]
        )
    )

    elements.append(
        Paragraph(
            shop.address or "",
            center_style
        )
    )

    elements.append(
        Paragraph(
            f"Tél : {shop.phone}",
            center_style
        )
    )

    elements.append(Spacer(1, 10))

    elements.append(
        HRFlowable(
            width="100%",
            thickness=1,
            color=colors.grey
        )
    )

    elements.append(Spacer(1, 15))

    # =========================
    # CLIENT + FACTURE INFOS
    # =========================
    invoice_number = (
        facture.reference
        if facture
        else f"FACT-{sale.id:05d}"
    )

    date_now = sale.created_at.strftime("%d/%m/%Y")

    customer_name = (
        sale.customer.full_name
        if sale.customer
        else sale.customer_name or "Client occasionnel"
    )

    customer_phone = (
        sale.customer.phone
        if sale.customer
        else sale.customer_phone or "-"
    )

    info_data = [[

        Paragraph(
            f"""
            <b>Client :</b><br/>
            {customer_name}<br/>
            {customer_phone}
            """,
            styles["Normal"]
        ),

        Paragraph(
            f"""
            <b>Facture :</b> {invoice_number}<br/>
            <b>Date :</b> {date_now}<br/>
            <b>Caissier :</b> {sale.user.username}
            """,
            right_style
        )

    ]]

    info_table = Table(
        info_data,
        colWidths=[3.5 * inch, 2.5 * inch]
    )

    elements.append(info_table)

    elements.append(Spacer(1, 20))

    # =========================
    # RESTAURANT INFO
    # =========================
    if sale.is_restaurant_order:

        restaurant_data = [[
            "Table",
            sale.restaurant_table.name if sale.restaurant_table else "-"
        ]]

        restaurant_table = Table(
            restaurant_data,
            colWidths=[2 * inch, 4 * inch]
        )

        restaurant_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))

        elements.append(restaurant_table)

        elements.append(Spacer(1, 15))

    # =========================
    # TABLE PRODUITS
    # =========================
    data = [[
        "Produit",
        "Qté",
        "Prix U.",
        "Total"
    ]]

    total_general = Decimal("0.00")

    for item in sale.items.all():

        total = item.quantity * item.selling_price

        total_general += total

        data.append([
            item.product.name,
            str(item.quantity),
            f"{item.selling_price:,.0f} {shop.currency}",
            f"{total:,.0f} {shop.currency}",
        ])

    table = Table(
        data,
        colWidths=[
            2.8 * inch,
            0.8 * inch,
            1.5 * inch,
            1.5 * inch
        ]
    )

    table.setStyle(TableStyle([

        ('BACKGROUND', (0, 0), (-1, 0), colors.black),

        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),

        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),

        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),

        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),

        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),

    ]))

    elements.append(table)

    elements.append(Spacer(1, 20))

    # =========================
    # TOTALS
    # =========================
    tva_rate = Decimal(shop.tva if shop.tva else 0)

    tva = total_general * (tva_rate / Decimal("100"))

    grand_total = total_general + tva

    amount_paid = (
        facture.amount_paid
        if facture
        else Decimal("0.00")
    )

    remaining = (
        facture.remaining
        if facture
        else grand_total
    )

    totals_data = [

        [
            "Sous-total :",
            f"{total_general:,.0f} {shop.currency}"
        ],

        [
            f"TVA ({tva_rate}%) :",
            f"{tva:,.0f} {shop.currency}"
        ],

        [
            "TOTAL :",
            f"{grand_total:,.0f} {shop.currency}"
        ],

        [
            "Montant payé :",
            f"{amount_paid:,.0f} {shop.currency}"
        ],

        [
            "Reste à payer :",
            f"{remaining:,.0f} {shop.currency}"
        ],

    ]

    totals_table = Table(
        totals_data,
        colWidths=[3.8 * inch, 2 * inch]
    )

    totals_table.setStyle(TableStyle([

        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),

        ('FONTNAME', (0, 2), (-1, 2), 'Helvetica-Bold'),

        ('LINEABOVE', (0, 2), (-1, 2), 1, colors.black),

        ('TEXTCOLOR', (0, 4), (-1, 4), colors.red),

    ]))

    elements.append(totals_table)

    elements.append(Spacer(1, 25))

    # =========================
    # STATUT FACTURE
    # =========================
    if facture:

        if facture.status == 'paid':
            statut = "FACTURE PAYÉE"

        elif facture.status == 'partial':
            statut = "PAIEMENT PARTIEL"

        elif facture.status == 'issued':
            statut = "NON PAYÉE"

        else:
            statut = "BROUILLON"

        elements.append(
            Paragraph(
                f"<b>Statut :</b> {statut}",
                styles["Heading3"]
            )
        )

        elements.append(Spacer(1, 15))

    # =========================
    # FOOTER
    # =========================
    elements.append(
        HRFlowable(
            width="100%",
            thickness=0.5,
            color=colors.grey
        )
    )

    elements.append(Spacer(1, 10))

    elements.append(
        Paragraph(
            "Merci pour votre confiance 🙂",
            center_style
        )
    )

    # =========================
    # BUILD PDF
    # =========================
    doc.build(elements)

    pdf = buffer.getvalue()

    buffer.close()

    response = HttpResponse(
        content_type='application/pdf'
    )

    response['Content-Disposition'] = (
        f'inline; filename="facture_{sale.id}.pdf"'
    )

    response.write(pdf)

    return response

@login_required
@role_required('Admin')
def generate_invoice(request, pk):
    pass


@login_required
@role_required('Admin', 'Caisse', 'Serveur')
@transaction.atomic
def sale_create(request):
    shop = ShopSettings.objects.first()
    # =========================================
    # GET OR CREATE SALE
    # =========================================
    sale_id = request.session.get('sale_id')

    if sale_id:
        sale = Sale.objects.filter(id=sale_id).first()

        if not sale:
            sale = Sale.objects.create(
                user=request.user,
                status='draft'
            )
            request.session['sale_id'] = sale.id

    else:
        sale = Sale.objects.create(
            user=request.user,
            status='draft'
        )
        request.session['sale_id'] = sale.id

    # =========================================
    # GET OR CREATE FACTURE
    # =========================================
    facture, created = Facture.objects.get_or_create(
        sale=sale,
        defaults={
            'customer': sale.customer,
            'total': sale.total_amount,
        }
    )

    # =========================================
    # FORMS
    # =========================================
    customers = Customer.objects.all()

    sale_form = SaleForm(instance=sale)
    form = SaleItemForm()

    # =========================================
    # POST
    # =========================================
    if request.method == "POST":

        customer_id = request.POST.get('customer')

        # =====================================
        # UPDATE CUSTOMER
        # =====================================
        if customer_id:

            customer = Customer.objects.filter(
                id=customer_id
            ).first()

            if customer:
                sale.customer = customer
                sale.save()

                # sync facture
                facture.customer = customer
                facture.save()

        # =====================================
        # SALE FORM
        # =====================================
        sale_form = SaleForm(
            request.POST,
            instance=sale
        )

        if sale_form.is_valid():

            sale = sale_form.save(commit=False)

            if customer_id:
                sale.customer = customer

            sale.save()

        # =====================================
        # ITEM FORM
        # =====================================
        form = SaleItemForm(request.POST)

        if form.is_valid():

            item = form.save(commit=False)

            item.sale = sale

            # snapshot prices
            item.selling_price = item.product.selling_price
            item.purchase_price = item.product.purchase_price

            # =================================
            # STOCK VALIDATION
            # =================================
            if item.quantity > item.product.stock:

                messages.warning(
                    request,
                    f"Stock insuffisant pour {item.product.name}."
                )

            else:

                # save item
                item.save()

                # =================================
                # UPDATE FACTURE
                # =================================
                sale.refresh_from_db()

                facture.total = sale.total_amount
                facture.customer = sale.customer

                # IMPORTANT
                facture.save()

                messages.success(
                    request,
                    "Produit ajouté à la vente."
                )

                return redirect('sale:sale_create')

    # =========================================
    # UPDATE FACTURE TOTAL
    # =========================================
    sale.refresh_from_db()

    facture.total = sale.total_amount
    facture.customer = sale.customer
    facture.save()

    # =========================================
    # DATA
    # =========================================
    items = sale.items.select_related(
        'product'
    ).all()

    context = {
        'sale': sale,
        'items': items,
        'sale_form': sale_form,
        'form': form,
        'shop': shop,
        'customers': customers,
        'facture': facture,
    }

    return render(
        request,
        'sale_create.html',
        context
    )

@login_required
@role_required('Admin', 'Caisse', 'Serveur')
def sale_finalize(request):
    sale_id = request.session.get('sale_id')

    if not sale_id:
        return redirect('sale:sale_create')

    sale = get_object_or_404(Sale, id=sale_id)

    sale.status = 'completed'
    sale.save()
    # Supprimer la session
    del request.session['sale_id']

    messages.success(request, "Vente finalisée avec succès.")
    return redirect('sale:sale_list')


@login_required
@role_required('Admin')
def sale_update(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    SaleForm = modelform_factory(Sale, fields=['user', 'customer_name', 'customer_phone'])

    if request.method == "POST":
        form = SaleForm(request.POST, instance=sale)
        if form.is_valid():
            form.save()
            messages.success(request, "Vente modifiée.")
            # return redirect('sale_detail', pk=sale.id)
            return redirect('sale:sale_list')
    else:
        form = SaleForm(instance=sale)
    context = {
        'form':form
    }
    return render(request, 'sale_form.html', context)


@login_required
@role_required('Admin')
def sale_delete(request, pk):
    sale = get_object_or_404(Sale, pk=pk)

    # Empêcher suppression si finalisée
    if sale.status == 'completed':
        messages.error(request, "Impossible de supprimer une vente finalisée.")
        return redirect('sale:sale_list')
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
        return redirect('sale:sale_create')
    context = {
        'sale':sale
    }
    return render(request, 'sale_delete.html', context)


@login_required
@role_required('Admin', 'Caisse', 'Serveur')
def saleitem_delete(request, pk):
    # Récupérer l'item
    item = get_object_or_404(SaleItem, id=pk)

    # Récupérer la vente avant suppression
    sale_id = item.sale.id

    if request.method == "POST":
        item.delete()  # Ton delete() remet déjà le stock
        messages.success(request, "Produit retiré de la vente.")
        return redirect('sale:sale_create')
    context = {
        'item':item
    }
    return render(request, 'saleitem_confirm_delete.html', context)


@login_required
@role_required('Admin', 'Caisse', 'Serveur')
def sale_detail(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    items = sale.items.all()
    shop = ShopSettings.objects.first()
    context = {
        'sale':sale,
        'items':items,
        'shop':shop,
    }
    return render(request, 'sale_detail.html', context)

@login_required
@role_required('Admin', 'Caisse')
def sale_invoice_pos(request, pk):
    sale = get_object_or_404(
        Sale,
        pk=pk,
        status='completed',
        # user=request.user
    )
    facture = get_object_or_404(Facture, sale=sale)
    shop = ShopSettings.objects.first()
    context = {
        'sale': sale,
        'facture': facture,
        'shop': shop,
    }

    return render(request, 'sale_invoice_pos.html', context)

@login_required
@role_required('Admin','Caisse')
def closing_report_view(request):
    report = closing_report(request.user)
    shop = ShopSettings.objects.first()
    today = timezone.now().date()

    credits_today = Facture.objects.filter(
        created_at__date=today,
        status__in=['issued', 'partial']
    )

    total_credit_today = sum(
        f.remaining for f in credits_today
    )
    context = {
        "report": report,
        "shop":shop,
        'credits_today': credits_today,
        'total_credit_today': total_credit_today,
    }
    return render(request, "closing_report.html", context)

@login_required
@role_required('Admin','Caisse')
def download_closing_pdf(request):
    pdf = generate_closing_pdf(user=request.user)

    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="closing_report.pdf"'

    return response

@login_required
@role_required('Admin', 'Caisse', 'Serveur')
@transaction.atomic
def create_restaurant_sale(request, table_id):

    table = get_object_or_404(
        RestaurantTable,
        id=table_id
    )

    # =====================================
    # CHECK EXISTING SALE
    # =====================================
    existing_sale = Sale.objects.filter(
        restaurant_table=table,
        status='draft',
        is_restaurant_order=True
    ).first()

    if existing_sale:

        # save session
        request.session['sale_id'] = existing_sale.id

        messages.info(
            request,
            f"Une commande existe déjà pour la table {table.name}."
        )

        return redirect('sale:sale_create')

    # =====================================
    # AUTO CUSTOMER
    # =====================================
    customer = table.customer

    # =====================================
    # CREATE SALE
    # =====================================
    sale = Sale.objects.create(

        user=request.user,

        status='draft',

        is_restaurant_order=True,

        restaurant_table=table,

        customer=customer,

        customer_name=(
            customer.full_name
            if customer
            else f"Table {table.name}"
        ),

        customer_phone=(
            customer.phone
            if customer
            else ""
        ),

        order_status='pending'
    )

    # =====================================
    # CREATE FACTURE
    # =====================================
    facture, created = Facture.objects.get_or_create(
        sale=sale,
        defaults={
            'customer': customer,
            'total': sale.total_amount,
        }
    )

    # =====================================
    # OCCUPY TABLE
    # =====================================
    table.status = 'occupied'
    table.save()

    # =====================================
    # STORE SESSION
    # =====================================
    request.session['sale_id'] = sale.id

    messages.success(
        request,
        f"Commande ouverte pour la table {table.name}."
    )

    # =====================================
    # REDIRECT TO POS SCREEN
    # =====================================
    return redirect('sale:sale_create')

@login_required
@role_required('Admin','Caisse','Serveur')
def update_order_status(request, sale_id, status):
    sale = get_object_or_404(Sale, id=sale_id)
    sale.order_status = status
    # si payé → vente finalisée
    if status == 'paid':
        sale.status = 'completed'

        # libérer table
        if sale.restaurant_table:
            sale.restaurant_table.status = 'free'
            sale.restaurant_table.save()

    sale.save()

    return redirect('sale:sale_detail', sale.id)



@login_required
@role_required('Admin','Caisse', 'Serveur')
def add_sale_item(request, sale_id):
    sale = get_object_or_404(Sale, id=sale_id)

    # empêcher modification si finalisée
    if sale.status == 'completed':

        messages.error(
            request,
            "Impossible de modifier une vente finalisée."
        )

        return redirect('sale:sale_detail', sale.id)

    products = Product.objects.filter(stock__gt=0)

    if request.method == 'POST':

        product_id = request.POST.get('product')
        quantity = int(request.POST.get('quantity', 1))

        product = get_object_or_404(Product, id=product_id)

        # Vérifier stock
        if quantity > product.stock:

            messages.error(
                request,
                f"Stock insuffisant pour {product.name}"
            )

            return redirect('sale:add_sale_item', sale.id)

        # Créer item
        SaleItem.objects.create(
            sale=sale,
            product=product,
            quantity=quantity,

            selling_price=product.selling_price,
            purchase_price=product.purchase_price,
        )

        messages.success(
            request,
            f"{product.name} ajouté à la commande."
        )

        return redirect('sale:sale_detail', sale.id)
    context = {
        'sale': sale,
        'products': products,
    }
    return render(request, 'add_sale_item.html', context)

@login_required
@role_required('Serveur', 'Admin')
def send_to_kitchen(request, sale_id):

    sale = get_object_or_404(
        Sale,
        id=sale_id
    )

    sale.order_status = 'sent'

    sale.save()

    messages.success(
        request,
        "Commande envoyée à la cuisine."
    )

    return redirect('dashboard:dashboard_serveur')

@login_required
@role_required('Admin', 'Cuisine')
def mark_preparing(request, sale_id):
    sale = get_object_or_404(
        Sale,
        id=sale_id
    )
    sale.order_status = 'preparing'
    sale.save()

    return redirect('dashboard:dashboard_cuisine')


@login_required
@role_required('Admin', 'Cuisine')
def mark_ready(request, sale_id):
    sale = get_object_or_404(
        Sale,
        id=sale_id
    )
    sale.order_status = 'ready'
    sale.save()
    return redirect('dashboard:dashboard_cuisine')