from django.contrib import admin
from .models import ShopSettings

# Register your models here.
class ShopSettingAdmin(admin.ModelAdmin):
	list_display = ('name','address','phone','currency','logo',)

admin.site.register(ShopSettings)