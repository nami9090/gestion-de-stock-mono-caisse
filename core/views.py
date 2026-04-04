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
