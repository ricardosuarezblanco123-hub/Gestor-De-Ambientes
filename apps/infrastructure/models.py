from django.db import models

class Sede(models.Model):
    nombre = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    descripcion = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='bi-building')

    def __str__(self):
        return self.nombre

class Ambiente(models.Model):
    nombre = models.CharField(max_length=100)
    sede = models.ForeignKey(Sede, on_delete=models.CASCADE, related_name='ambientes')
    inventario = models.TextField(blank=True, null=True, verbose_name="Inventario del ambiente")

    def __str__(self):
        return f"{self.nombre} ({self.sede.nombre})"