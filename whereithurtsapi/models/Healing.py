"""Database Healing module"""
from django.db import models
from whereithurtsapi.models import Treatment

class Healing(models.Model):
    """Database Healing model"""

    patient = models.ForeignKey("Patient", on_delete=models.CASCADE)
    notes = models.CharField(max_length=300)
    duration = models.IntegerField()
    added_on = models.DateTimeField()

    @property
    def treatments(self):
        healing_treatments = self.healing_treatments.all()
        return [ht.treatment for ht in healing_treatments]
    
        
