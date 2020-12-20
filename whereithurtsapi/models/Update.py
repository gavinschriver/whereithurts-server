""" Database module for Updates """
from django.db import models

class Update(models.Model):
    
    hurt = models.ForeignKey("Hurt", on_delete=models.CASCADE)
    added_on = models.DateTimeField()
    pain_level = models.IntegerField()
    notes = models.CharField(max_length=300)

    @property
    def is_first_update(self):
        if self.hurt.first_update_id == self.id:
            return True
        return False
