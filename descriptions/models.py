from django.db import models

# Create your models here.

class AudioDescription(models.Model):
    input_text = models.CharField(max_length=255)  # Movie title or YouTube URL
    input_type = models.CharField(max_length=10)   # 'movie' or 'youtube'
    description_length = models.CharField(max_length=10)  # 'short', 'medium', or 'long'
    description_text = models.TextField()
    audio_url = models.CharField(max_length=255, null=True, blank=True)  # Store the path to the audio file
    created_at = models.DateTimeField(auto_now_add=True)
    user_id = models.CharField(max_length=255)  # Store the Firebase user ID

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.input_type}: {self.input_text} ({self.description_length})"
