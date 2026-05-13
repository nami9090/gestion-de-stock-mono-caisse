from django.contrib import admin
from .models import RestaurantTable

# Register your models here.
@admin.register(RestaurantTable)
class RestaurentTableAdmin(admin.ModelAdmin):
	list_display = ('name', 'capacity', 'status')