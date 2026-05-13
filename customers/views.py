from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from .forms import CustomerForm
from .models import Customer

from sales.models import Sale
from core.models import ShopSettings
from accounts.decorators import role_required
from django.contrib.auth.decorators import login_required


# =========================
# LISTE CLIENTS
# =========================
@login_required
@role_required('Admin', 'Caisse')
def customer_list(request):
    query = request.GET.get('q')
    customers = Customer.objects.all()
    if query:
        customers = customers.filter(full_name__icontains=query)

    context = {
        'customers': customers
    }
    return render(request, 'customer_list.html', context)


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
    customer = get_object_or_404(Customer,pk=pk)
    sales = Sale.objects.filter(customer=customer).order_by('-created_at')
    shop = ShopSettings.objects.first()
    total_spent = sum(
        sale.total_amount
        for sale in sales
    )

    context = {
        'customer': customer,
        'sales': sales,
        'total_spent': total_spent,
        'shop':shop,
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