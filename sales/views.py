from django.forms import modelform_factory
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from accounts.decorators import role_required
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Sale, SaleItem
from .forms import SaleForm, SaleItemForm

from core.models import ShopSettings

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
@role_required('Admin','Caisse')
def sale_list(request):
    if request.user.is_superuser:
        sales = Sale.objects.filter(status='completed').order_by('-created_at')
    else:
        sales = Sale.objects.filter(
            status='completed',
            user=request.user
        ).order_by('-created_at')
    shop = ShopSettings.objects.first()
    context = {
        'sales':sales,
        'shop':shop,
    }
    return render(request, 'sale_list.html', context)


@login_required
@role_required('Admin', 'Caisse')
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
@role_required('Admin', 'Caisse')
def sale_create(request):
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
                return redirect('sale:sale_create')

    items = sale.items.all()

    context = {
        'sale': sale,
        'items': items,
        'sale_form':sale_form,
        'form': form,
        'shop':shop
    }
    return render(request, 'sale_create.html', context)


@login_required
@role_required('Admin', 'Caisse')
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
@role_required('Admin', 'Caisse')
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
@role_required('Admin', 'Caisse')
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
        user=request.user
    )

    shop = ShopSettings.objects.first()
    context = {
        'sale':sale,
        'shop':shop,
    }
    return render(request,'sale_invoice_pos.html', context)