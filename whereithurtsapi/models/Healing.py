"""Database Healing module"""
from django.db import models

class Healing(models.Model):
    """Database Healing model"""

    patient = models.ForeignKey("Patient", on_delete=models.CASCADE)
    notes = models.CharField(max_length=300)
    duration = models.IntegerField()
    added_on = models.DateTimeField()
    
