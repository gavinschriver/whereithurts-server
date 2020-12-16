"""Database Healing module"""
from django.db import models

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
    
    @property
    def hurts(self):
        hurt_healings = self.hurt_healings.all()
        return [hh.hurt for hh in hurt_healings]

    @property
    def date_added(self):
        return self.added_on.strftime('%-m/%d/%Y')
