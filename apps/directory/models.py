from django.db import models

class people(models.Model):
    code = models.CharField(max_length=20, unique=True)
    full_name = models.CharField(max_length=200)
    position = models.CharField(max_length=100, blank=True)
    
    class Meta:
        db_table = 'directory_people'