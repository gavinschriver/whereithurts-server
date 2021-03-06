""" Database module for HealingTreatments """
from django.db import models

class HealingTreatment(models.Model):
    healing = models.ForeignKey("Healing", related_name="healing_treatments", on_delete=models.CASCADE)
    treatment = models.ForeignKey("Treatment", related_name="healing_treatments", on_delete=models.CASCADE)