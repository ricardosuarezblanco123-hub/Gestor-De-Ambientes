from django.db import models

class headquarters(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    
    class Meta:
        db_table = 'infrastructure_headquarters'

class environments(models.Model):
    name = models.CharField(max_length=100)
    headquarters_id = models.ForeignKey('headquarters', on_delete=models.CASCADE)
    
    class Meta:
        db_table = 'infrastructure_environments'