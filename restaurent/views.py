from django.shortcuts import render, get_object_or_404, redirect
from .models import RestaurantTable
from sales.models import Sale

from accounts.decorators import role_required
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import RestaurantTableForm

# Create your views here.

# =========================
# LISTE TABLES
# =========================
@login_required
@role_required('Admin','Caisse')
def table_list(request):
    tables = RestaurantTable.objects.all()
    context = {
    	'tables': tables
    }
    return render(request, 'table_list.html', context)


# =========================
# DETAIL TABLE
# =========================
@login_required
@role_required('Admin','Caisse')
def table_detail(request, pk):
    table = get_object_or_404(RestaurantTable, pk=pk)
    sales = Sale.objects.filter(
        restaurant_table=table,
        status='draft'
    ).order_by('-created_at')
    context = {
    	'table':table,
    	'sales':sales
    }
    return render(request, 'table_detail.html', context)


# =========================
# MODIFIER TABLE
# =========================
@login_required
@role_required('Admin','Caisse')
def table_update(request, pk):
    table = get_object_or_404(RestaurantTable,pk=pk)
    form = RestaurantTableForm(request.POST or None,instance=table)
    if form.is_valid():
        form.save()
        messages.success(request,"Table modifiée.")
        return redirect('restaurant:table_list')

    context = {
        'form': form,
        'table': table
    }
    return render(request,'table_form.html',context)


# =========================
# SUPPRESSION TABLE
# =========================
@login_required
@role_required('Admin')
def table_delete(request, pk):
    table = get_object_or_404(RestaurantTable,pk=pk)
    if request.method == "POST":
        table.delete()
        messages.success(request,"Table supprimée.")
        return redirect('restaurant:table_list')

    context = {
        'table': table
    }
    return render(request,'table_delete.html',context)


# OUVRIR TABLE
@login_required
@role_required('Admin','Caisse')
def open_table(request, pk):
    table = get_object_or_404(RestaurantTable, pk=pk)
    table.status = 'occupied'
    table.save()
    return redirect('restaurant:table_detail', pk=table.pk)


# LIBERER TABLE
@login_required
@role_required('Admin','Caisse')
def close_table(request, pk):
    table = get_object_or_404(RestaurantTable, pk=pk)
    table.status = 'free'
    table.save()
    return redirect('restaurant:table_list')


# =========================
# CREATION TABLE
# =========================
@login_required
@role_required('Admin')
def table_create(request):
    form = RestaurantTableForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request,"Table ajoutée.")
        return redirect('restaurant:table_list')
    context = {
        'form': form
    }
    return render(request, 'table_form.html', context)

@login_required
@role_required('Admin','Caisse')
def delete_sale(request, sale_id):
    sale = get_object_or_404(
        Sale,
        id=sale_id
    )
    table_id = None
    if sale.restaurant_table:
        table_id = sale.restaurant_table.id

    # remettre stock
    for item in sale.items.all():
        product = item.product
        product.stock += item.quantity
        product.save()

    sale.delete()
    messages.success(request,"Commande supprimée.")

    if table_id:

        return redirect('restaurant:table_detail',table_id)

    return redirect('sale:sale_list')

