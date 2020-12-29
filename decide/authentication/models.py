from django.conf import settings
from django.db import models

from django.db.models.fields import CharField, URLField, DateTimeField

# Create your models here.
class EmailToken(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, unique=True,
        on_delete=models.CASCADE, verbose_name="User"
    )
    secret = CharField(max_length=32, verbose_name="Secret Key")
    callback = URLField(verbose_name="Callback")
    created = DateTimeField("Created", auto_now_add=True)

    def __str__(self):
        return self.secret