""" Database Hurt module """
from django.db import models

class Hurt(models.Model):
    """Database Hurt model"""

    patient = models.ForeignKey("Patient", on_delete=models.CASCADE)
    bodypart = models.ForeignKey("Bodypart", on_delete=models.DO_NOTHING)
    name = models.CharField(max_length=100)
    added_on = models.DateTimeField()
    is_active = models.BooleanField()
    
