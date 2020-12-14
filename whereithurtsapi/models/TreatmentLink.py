""" Database module for TreatmentLinks """
from django.db import models

class TreatmentLink(models.Model):
    treatment = models.ForeignKey("Treatment", on_delete=models.CASCADE)
    linktext = models.CharField(max_length=75)
    linkurl = models.CharField(max_length=150)
