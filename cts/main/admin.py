from django.contrib import admin

# Register your models here.
from .models import Camera, CableSettings

admin.site.register(Camera)
@admin.register(CableSettings)
class CableSettingsAdmin(admin.ModelAdmin):
    list_display = ['price_per_meter', 'is_active']
    list_editable = ['is_active']
