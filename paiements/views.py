from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from decimal import Decimal

from factures.models import Facture
from .models import Paiement
from .forms import PaiementForm

from accounts.decorators import role_required
from core.models import ShopSettings

# Create your views here.
@login_required
@role_required('Admin', 'Caisse')
def paiement_list(request, facture_id=None):
    shop = ShopSettings.objects.first()

    if facture_id:
        facture = get_object_or_404(Facture, id=facture_id)
        paiements = facture.paiements.select_related('facture').all()
    else:
        facture = None
        paiements = Paiement.objects.select_related('facture').order_by('-created_at')

    context = {
        "paiements": paiements,
        "facture": facture,
        "shop": shop,
    }
    return render(request, "paiement_list.html", context)


@login_required
@role_required('Admin', 'Caisse')
def paiement_create(request, facture_id):

    facture = get_object_or_404(Facture, id=facture_id)
    shop = ShopSettings.objects.first()

    if request.method == "POST":

        form = PaiementForm(request.POST)

        if form.is_valid():

            paiement = form.save(commit=False)

            montant = paiement.montant

            # validation métier
            if montant <= 0:
                messages.error(request, "Montant invalide.")
                return redirect('paiement:paiement_create', facture.id)

            if montant > facture.remaining:
                messages.error(request, "Montant supérieur au reste.")
                return redirect('paiement:paiement_create', facture.id)

            paiement.facture = facture
            paiement.save()

            facture.recalc_payments()

            messages.success(request, "Paiement enregistré.")

            return redirect('facture:facture_detail', facture.id)

    else:
        form = PaiementForm()

    context = {
        "form": form,
        "facture": facture,
        "shop": shop,
    }
    return render(request, "paiement_form.html", context)

@login_required
@role_required('Admin', 'Caisse')
def paiement_update(request, pk):

    paiement = get_object_or_404(Paiement, id=pk)
    facture = paiement.facture
    shop = ShopSettings.objects.first()

    if request.method == "POST":
        form = PaiementForm(request.POST, instance=paiement)

        if form.is_valid():
            form.save()

            facture.recalc_payments()

            messages.success(request, "Paiement modifié.")
            return redirect('paiement:paiement_list')

    else:
        form = PaiementForm(instance=paiement)

    context = {
        "form": form,
        "facture": facture,
        "paiement": paiement,
        "shop": shop,
    }
    return render(request, "paiement_form.html", context)

@login_required
@role_required('Admin', 'Caisse')
def paiement_delete(request, pk):
    shop = ShopSettings.objects.first()
    paiement = get_object_or_404(Paiement, id=pk)
    facture = paiement.facture

    if request.method == "POST":

        paiement.delete()

        facture.recalc_payments()

        messages.success(request, "Paiement supprimé.")
        return redirect('paiement:paiement_list')

    context = {
        "paiement": paiement,
        "facture": facture,
        "shop":shop,
    }
    return render(request, "paiement_confirm_delete.html", context)

@login_required
@role_required('Admin', 'Caisse')
def paiement_detail(request, pk):
    shop = ShopSettings.objects.first()
    paiement = get_object_or_404(Paiement, id=pk)
    facture = paiement.facture

    context = {
        "paiement": paiement,
        "facture": facture,
        "shop": shop,
    }
    return render(request, "paiement_detail.html", context)