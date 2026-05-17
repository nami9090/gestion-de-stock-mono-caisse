from django import forms
from .models import Facture


class FactureForm(forms.ModelForm):
    class Meta:
        model = Facture
        fields = ['customer', 'total', 'amount_paid', 'status']
        widgets = {
            'customer': forms.Select({'class':'form-control'}),
            'total': forms.NumberInput({'class':'form-control'}),
            'amount_paid': forms.NumberInput({'class':'form-control'}),
            'status': forms.Select({'class':'form-control'}),
        }