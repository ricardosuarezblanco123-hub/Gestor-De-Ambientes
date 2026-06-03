from django.db import models
from apps.infrastructure.models import Ambiente

class Reserva(models.Model):
    ambiente = models.ForeignKey(Ambiente, on_delete=models.CASCADE)
    instructor = models.ForeignKey('directory.Instructor', on_delete=models.CASCADE)
    materia = models.CharField(max_length=150, null=True, blank=True)
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    # Cambiamos a tu modelo personalizado
    user = models.ForeignKey('accounts.user', on_delete=models.CASCADE)
    jornada = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.ambiente.nombre} - {self.instructor}"