from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import Facture
from .forms import FactureForm
from accounts.decorators import role_required
from core.models import ShopSettings


@login_required
@role_required('Admin', 'Caisse')
def facture_list(request):
    shop = ShopSettings.objects.first()
    factures = Facture.objects.select_related('sale', 'customer').order_by('-created_at')
    context = {
        "factures": factures,
        'shop': shop,
    }
    return render(request, "facture_list.html", context)

@login_required
@role_required('Admin', 'Caisse')
def facture_detail(request, pk):
    shop = ShopSettings.objects.first()
    facture = get_object_or_404(
        Facture.objects.select_related('sale', 'customer'),
        id=pk
    )
    paiements = facture.paiements.all()
    context = {
        "facture": facture,
        "paiements": paiements,
        "shop":shop,

    }
    return render(request, "facture_detail.html", context)


@login_required
@role_required('Admin', 'Caisse')
def facture_create(request):
    if request.method == "POST":
        form = FactureForm(request.POST)
        if form.is_valid():
            facture = form.save()
            messages.success(request, "Facture créée avec succès.")
            return redirect('facture:facture_list')

    else:
        form = FactureForm()
    context = {
        "form": form
    }
    return render(request, "facture_form.html", context)


@login_required
@role_required('Admin', 'Caisse')
def facture_update(request, pk):
    facture = get_object_or_404(Facture, id=pk)
    if request.method == "POST":
        form = FactureForm(request.POST, instance=facture)
        if form.is_valid():
            facture = form.save()
            #recalcul automatique statut
            facture.update_status()
            messages.success(request, "Facture mise à jour.")
            return redirect('facture:facture_detail', facture.id)
    else:
        form = FactureForm(instance=facture)
    context = {
        "form": form,
        "facture": facture,
    }
    return render(request, "facture_form.html", context)


@login_required
@role_required('Admin')
def facture_delete(request, pk):
    facture = get_object_or_404(Facture, id=pk)
    if request.method == "POST":
        facture.delete()
        messages.success(request, "Facture supprimée.")
        return redirect('facture:facture_list')
    context = {
        "facture": facture
    }
    return render(request, "facture_confirm_delete.html", context)