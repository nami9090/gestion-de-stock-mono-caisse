from django import forms
from .models import Paiement


class PaiementForm(forms.ModelForm):
    class Meta:
        model = Paiement
        fields = ['montant', 'mode_paiement']
        widgets = {
            'montant': forms.NumberInput(attrs={'class':'form-control'}),
            'mode_paiement': forms.Select(attrs={'class':'form-control'}),
        }