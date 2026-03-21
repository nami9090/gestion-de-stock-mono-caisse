from django import forms
from .models import ShopSettings

class ShopSettingsForm(forms.ModelForm):
    class Meta:
        model = ShopSettings
        fields = ['name', 'address', 'phone', 'currency','tva','logo']  # adapte selon ton modèle
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'currency': forms.Select(attrs={'class': 'form-control'}),
            'tva': forms.TextInput(attrs={'class': 'form-control'}),
            'logo': forms.ClearableFileInput(attrs={'class':'form-control', 'accept':'image/*'})
        }