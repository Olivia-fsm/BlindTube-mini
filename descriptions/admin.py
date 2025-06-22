from django.contrib import admin
from .models import AudioDescription

@admin.register(AudioDescription)
class AudioDescriptionAdmin(admin.ModelAdmin):
    list_display = ('input_text', 'input_type', 'description_length', 'audio_url', 'created_at', 'user_id')
    list_filter = ('input_type', 'description_length', 'created_at')
    search_fields = ('input_text', 'description_text', 'audio_url', 'user_id')
    readonly_fields = ('created_at',)
