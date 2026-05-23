from django.contrib import admin
from .models import UserActivityLog, Profile
# Register your models here.
class UserActivityAdmin(admin.ModelAdmin):
	list_display = ('user', 'action', 'description')

class ProfileAdmin(admin.ModelAdmin):
	list_display = ('user', 'image')

admin.site.register(UserActivityLog, UserActivityAdmin)
admin.site.register(Profile, ProfileAdmin)