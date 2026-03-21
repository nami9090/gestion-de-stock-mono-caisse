from django.contrib import admin
from .models import Sale, SaleItem
# Register your models here.

class SaleAdmin(admin.ModelAdmin):
	list_display = ('status','total_amount','total_profit','user',)

class SaleItemAdmin(admin.ModelAdmin):
	list_display = ('sale','product','quantity','selling_price','purchase_price',)

admin.site.register(Sale, SaleAdmin)
admin.site.register(SaleItem, SaleItemAdmin)