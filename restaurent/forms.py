from django import forms
from .models import RestaurantTable


class RestaurantTableForm(forms.ModelForm):

    class Meta:
        model = RestaurantTable
        fields = ['name', 'capacity', 'status', 'customer']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control'
            }),

            'capacity': forms.NumberInput(attrs={
                'class': 'form-control'
            }),

            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'customer': forms.Select(attrs={
                'class': 'form-select'
            })
        }