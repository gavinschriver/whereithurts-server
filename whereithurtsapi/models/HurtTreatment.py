""" Database module for HurtTreatments """
from django.db import models

class HurtTreatment(models.Model):
    hurt = models.ForeignKey("Hurt", related_name="hurt_treatments", on_delete=models.CASCADE)
    treatment = models.ForeignKey("Treatment", related_name="hurt_treatments", on_delete=models.CASCADE)