from django.db import models

# Create your models here.

class AudioDescription(models.Model):
    TTS_PROVIDER_CHOICES = [
        ('google', 'Google TTS'),
        ('eleven_labs', 'Eleven Labs'),
        ('hume', 'Hume.ai')
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    audio_url = models.CharField(max_length=255, null=True, blank=True)
    tts_provider = models.CharField(
        max_length=20,
        choices=TTS_PROVIDER_CHOICES,
        null=True,
        blank=True,
        help_text="The TTS provider used to generate the audio"
    )

    def __str__(self):
        provider_tag = f" [{self.tts_provider}]" if self.tts_provider else ""
        return f"{self.title}{provider_tag}"
