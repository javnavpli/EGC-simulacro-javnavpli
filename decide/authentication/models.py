from django.db import models
from django.contrib.auth.models import User

# Create your models here.

#Extra: Atributos extras para el modelo User
class Extra(models.Model):
    id = models.AutoField(primary_key=True)
    phone = models.CharField(null = False, max_length = 100, verbose_name='Telefono',unique=True)
    totp_code = models.CharField(max_length = 50, null=True, blank=True, verbose_name='Codigo 2fa por tiempo')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    def __str__(self):
        return self.phone