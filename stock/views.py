from django.shortcuts import render, redirect
from accounts.decorators import role_required
from django.contrib.auth.decorators import login_required

from .models import StockEntry
from .forms import StockEntryForm

# Create your views here.
@login_required
@role_required('Admin')
def stock_list(request):
    stocks = StockEntry.objects.select_related('product', 'supplier', 'user').order_by('-date')
    context = {
        'stocks':stocks
    }
    return render(request, 'stock_list.html', context)

@login_required
@role_required('Admin')
def stock_create(request):
    form = StockEntryForm(request.POST or None)
    if form.is_valid():
        stock_entry = form.save(commit=False)
        stock_entry.user = request.user
        stock_entry.save()
        return redirect('stock:stock_list')
    context = {
        'form':form
    }
    return render(request, 'stock_form.html', context)