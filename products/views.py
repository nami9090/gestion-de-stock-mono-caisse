from django.shortcuts import render, redirect, get_object_or_404
from accounts.decorators import role_required
from django.contrib.auth.decorators import login_required

from core.models import ShopSettings

from .models import Product, Category
from .forms import ProductForm, CategoryForm

# Create your views here.
@login_required
@role_required('Admin','Caisse')
def product_list(request):
    products = Product.objects.all().order_by('-created_at')
    shop = ShopSettings.objects.first()
    context = {
        'produits':products,
        'shop':shop
    }
    return render(request, 'product_list.html', context)

@login_required
@role_required('Admin')
def product_create(request):
    form = ProductForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('products:product_list')
    context = {
        'form':form
    }
    return render(request, 'product_form.html', context)

@login_required
@role_required('Admin')
def product_update(request, pk):
    product = get_object_or_404(Product, pk=pk)
    form = ProductForm(request.POST or None, instance=product)
    if form.is_valid():
        form.save()
        return redirect('products:product_list')
    context = {
        'form':form
    }
    return render(request, 'product_form.html', context)

@login_required
@role_required('Admin')
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.delete()
        return redirect('products:product_list')
    context = {
        'product':product
    }
    return render(request, 'product_confirm_delete.html', context)

@login_required
@role_required('Admin')
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    context = {
        'product':product
    }
    return render(request, 'product_details.html', context)

@login_required
@role_required('Admin')
def category_list(request):
    categories = Category.objects.all().order_by('name')
    context = {
        'categories':categories
    }
    return render(request, 'category_list.html', context)

@login_required
@role_required('Admin')
def category_create(request):
    form = CategoryForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('products:category_list')
    context = {
        'form':form
    }
    return render(request, 'category_form.html', context)

@login_required
@role_required('Admin')
def category_update(request, pk):
    categorie = get_object_or_404(Category, pk=pk)
    form = ProductForm(request.POST or None, instance=categorie)
    if form.is_valid():
        form.save()
        return redirect('products:category_list')
    context = {
        'form':form
    }
    return render(request, 'category_form.html', context)

@login_required
@role_required('Admin')
def category_delete(request, pk):
    categorie = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        categorie.delete()
        return redirect('products:category_list')
    context = {
        'category':categorie
    }
    return render(request, 'category_confirm_delete.html', context)