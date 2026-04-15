from django import forms
from decimal import Decimal
from .models import Sale, SaleItem

class SaleForm(forms.ModelForm):
    class Meta:
        model = Sale
        # On ne veut pas modifier total_amount, total_profit, created_at
        fields = ['customer_name', 'customer_phone']  # éventuellement juste 'user'
        widgets = {
            'customer_name': forms.TextInput(attrs={'class': 'form-control'}),
            'customer_phone': forms.TextInput(attrs={'class': 'form-control'}),
        }

class SaleItemForm(forms.ModelForm):
    class Meta:
        model = SaleItem
        fields = ['product', 'quantity']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
        }
