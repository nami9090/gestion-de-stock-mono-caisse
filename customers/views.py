from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from .forms import CustomerForm
from .models import Customer

from django.db.models import (
    Sum,
    F,
    Q,
    DecimalField,
    ExpressionWrapper,
    Value
)
from django.core.paginator import Paginator
from django.db.models.functions import Coalesce
from factures.models import Facture
from core.models import ShopSettings
from sales.models import Sale
from core.models import ShopSettings
from accounts.decorators import role_required
from django.contrib.auth.decorators import login_required

@login_required
@role_required('Admin', 'Caisse')
def customer_list(request):
    search = request.GET.get('search', '')
    shop = ShopSettings.objects.first()
    # ====================================
    # CLIENTS + TOTAL IMPAYÉ
    # ====================================
    customers = Customer.objects.annotate(
        total_impaye=Coalesce(
            Sum(
                ExpressionWrapper(
                    F('facture__total') - F('facture__amount_paid'),
                    output_field=DecimalField(
                        max_digits=12,
                        decimal_places=2
                    )
                ),

                filter=Q(
                    facture__status__in=['issued', 'partial']
                )
            ),
            # IMPORTANT FIX
            Value(
                0,
                output_field=DecimalField(
                    max_digits=12,
                    decimal_places=2
                )
            )
        )

    ).order_by('-id')
    # ====================================
    # SEARCH
    # ====================================
    if search:
        customers = customers.filter(
            Q(full_name__icontains=search) |
            Q(phone__icontains=search) |
            Q(email__icontains=search)
        )
    # ================= PAGINATION =================
    paginator = Paginator(customers, 20)
    page_number = request.GET.get('page')
    customers = paginator.get_page(page_number)
    context = {
        'customers': customers,
        'search': search,
        'shop':shop
    }
    return render(request,'customer_list.html',context)

# =========================
# CREATION CLIENT
# =========================
@login_required
@role_required('Admin', 'Caisse')
def customer_create(request):
    form = CustomerForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request,"Client ajouté avec succès.")
        return redirect('customer:customer_list')

    context = {
        'form': form
    }
    return render(request, 'customer_form.html', context)


# =========================
# DETAIL CLIENT
# =========================
@login_required
@role_required('Admin', 'Caisse')
def customer_detail(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    sales = Sale.objects.filter(
        customer=customer
    ).order_by('-created_at')
    
    # =====================================
    # FACTURES CLIENT
    # =====================================
    factures = Facture.objects.filter(
        customer=customer
    ).order_by('-created_at')
    
    # =====================================
    # FACTURES IMPAYEES
    # =====================================

    factures_impayees = factures.filter(
        status__in=['issued', 'partial']
    )

    # TOTAL RESTANT À PAYER
    total_impaye = sum(
        facture.total - facture.amount_paid
        for facture in factures_impayees
    )
    # =====================================
    # TOTAL SPENT
    # =====================================
    total_spent = sum(
        sale.total_amount for sale in sales
    )
    shop = ShopSettings.objects.first()
    context = {
        'customer': customer,
        'sales': sales,

        # FACTURES
        'factures': factures,
        'factures_impayees': factures_impayees,
        'total_impaye': total_impaye,

        # SALES
        'total_spent': total_spent,
        'shop': shop,
    }
    return render(request,'customer_detail.html',context)


# =========================
# MODIFIER CLIENT
# =========================
@login_required
@role_required('Admin', 'Caisse')
def customer_update(request, pk):
    customer = get_object_or_404(Customer,pk=pk)

    form = CustomerForm(request.POST or None,instance=customer)

    if form.is_valid():
        form.save()
        messages.success(request,"Client modifié.")
        return redirect('customer:customer_list')

    context = {
        'form': form,
        'customer': customer
    }
    return render(request,'customer_form.html',context)


# =========================
# SUPPRESSION CLIENT
# =========================
@login_required
@role_required('Admin', 'Caisse')
def customer_delete(request, pk):
    customer = get_object_or_404(Customer,pk=pk)
    if request.method == "POST":
        customer.delete()
        messages.success(request,"Client supprimé.")
        return redirect('customer:customer_list')

    context = {
        'customer': customer
    }
    return render(request,'customer_delete.html',context)