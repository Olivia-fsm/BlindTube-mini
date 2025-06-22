from rest_framework import serializers
from .models import AudioDescription

class AudioDescriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AudioDescription
        fields = ['id', 'input_text', 'input_type', 'description_length', 'description_text', 'audio_url', 'created_at', 'user_id']
        read_only_fields = ['created_at'] 