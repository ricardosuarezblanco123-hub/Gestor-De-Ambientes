from django.db import models

class role(models.Model):
    name = models.CharField(max_length=50, unique=True)
    
    class Meta:
        db_table = 'accounts_role'

class user(models.Model):
    username = models.CharField(max_length=150, unique=True)
    password = models.CharField(max_length=128)
    email = models.EmailField(unique=True, null=True, blank=True)
    # Cambiamos role_id a role para evitar que Django cree una columna llamada role_id_id
    role = models.ForeignKey('role', on_delete=models.CASCADE, null=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'accounts_user'