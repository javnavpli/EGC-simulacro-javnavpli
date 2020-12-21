from django.db import models

# Create your models here.

#Extra: Atributos extras para el modelo User
class Extra(models.Model)
    id = models.AutoField(primary_key=True)
    phone = models.CharField(required = True, max_length = 100, label='Telefono',unique=True)
    double_authentication = models.BooleanField(required=True, label = 'Doble autenticación')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    def __str__(self):
        return self.phone