"""Database TreatmentType module"""
from django.db import models

class TreatmentType(models.Model):
    """Database TreatmentType model
    
    Defined internally"""
    name = models.CharField(max_length=50)
