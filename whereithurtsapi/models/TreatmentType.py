"""Database TreatmentType module"""
from django.db import models

class TreatmentType(models.Model):
    """Database TreatmentType model
    
    Defined internally"""
    name = models.CharField(max_length=50)
    image = models.ImageField(upload_to='icons/treatmenttypes', height_field=None, width_field=None, null=True, max_length=None)
