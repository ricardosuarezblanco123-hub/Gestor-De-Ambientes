from django.db import models

class reserves(models.Model):
    user_id = models.ForeignKey('accounts.user', on_delete=models.CASCADE)
    environments_id = models.ForeignKey('infrastructure.environments', on_delete=models.CASCADE)
    people_id = models.ForeignKey('directory.people', on_delete=models.SET_NULL, null=True, blank=True)
    start_date = models.DateField()
    end_date = models.DateField()
    
    class Meta:
        db_table = 'bookings_reserves'
        unique_together = ['environments_id', 'start_date', 'end_date']

class days(models.Model):
    reserves_id = models.ForeignKey('reserves', on_delete=models.CASCADE)
    date = models.DateField()
    
    class Meta:
        db_table = 'bookings_days'
        unique_together = ['reserves_id', 'date']